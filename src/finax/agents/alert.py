"""Alert Agent — delivers the daily digest via Telegram and email."""

import asyncio
import logging
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from finax.config import settings
from finax.state import AnalyzedArticle, FinaxState, SentimentSummary

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
SENTIMENT_EMOJI = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _escape_mdv2(text: str) -> str:
    """Escape all MarkdownV2 reserved characters."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


def _format_telegram(
    summary: SentimentSummary,
    analyzed: list[AnalyzedArticle],
    run_timestamp: datetime,
) -> str:
    date_str = _escape_mdv2(run_timestamp.strftime("%Y-%m-%d"))
    lines: list[str] = [
        f"*📊 Finax Daily Digest — {date_str}*",
        "",
        f"🟢 Bullish: *{summary.bullish_count}*  "
        f"🔴 Bearish: *{summary.bearish_count}*  "
        f"⚪ Neutral: *{summary.neutral_count}*",
        "",
        "*Market Outlook*",
        _escape_mdv2(summary.market_outlook),
    ]

    if summary.top_movers:
        lines += ["", "*Top Movers*", _escape_mdv2(", ".join(summary.top_movers))]

    # Top 5 articles
    top_articles = sorted(analyzed, key=lambda a: a.confidence, reverse=True)[:5]
    if top_articles:
        lines += ["", "*Top Stories*"]
        for art in top_articles:
            emoji = SENTIMENT_EMOJI.get(art.sentiment, "⚪")
            title = _escape_mdv2(art.article.title[:100])
            source = _escape_mdv2(art.article.source_name)
            conf = _escape_mdv2(f"{art.confidence:.0%}")
            lines.append(f"{emoji} {title} \\({source}, {conf}\\)")

    message = "\n".join(lines)

    # Telegram hard limit is 4096 chars; truncate safely
    if len(message) > 4000:
        message = message[:3997] + "\\.\\.\\."

    return message


def _format_email(
    summary: SentimentSummary,
    analyzed: list[AnalyzedArticle],
    run_timestamp: datetime,
) -> tuple[str, str]:
    """Returns (plain_text, html_body)."""
    date_str = run_timestamp.strftime("%Y-%m-%d %H:%M UTC")

    # --- Plain text ---
    plain_lines = [
        f"Finax Daily Digest — {date_str}",
        "=" * 50,
        f"Bullish: {summary.bullish_count} | Bearish: {summary.bearish_count} | Neutral: {summary.neutral_count}",
        "",
        "Market Outlook",
        "-" * 30,
        summary.market_outlook,
        "",
    ]
    if summary.top_movers:
        plain_lines += ["Top Movers: " + ", ".join(summary.top_movers), ""]

    plain_lines.append("Top Stories")
    plain_lines.append("-" * 30)
    top_articles = sorted(analyzed, key=lambda a: a.confidence, reverse=True)[:10]
    for art in top_articles:
        plain_lines.append(
            f"[{art.sentiment.upper()}] {art.article.title} ({art.article.source_name})"
        )
        plain_lines.append(f"  {art.article.url}")
        plain_lines.append(f"  {art.reasoning}")
        plain_lines.append("")

    plain = "\n".join(plain_lines)

    # --- HTML ---
    rows = "".join(
        f"<tr>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{art.article.title}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{art.article.source_name}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eee;color:{'#16a34a' if art.sentiment=='bullish' else '#dc2626' if art.sentiment=='bearish' else '#6b7280'}'>"
        f"{art.sentiment.capitalize()}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{art.confidence:.0%}</td>"
        f"</tr>"
        for art in top_articles
    )

    top_mover_html = (
        f"<p><strong>Top Movers:</strong> {', '.join(summary.top_movers)}</p>"
        if summary.top_movers
        else ""
    )

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;color:#1f2937">
  <h2 style="color:#1d4ed8">📊 Finax Daily Digest — {date_str}</h2>
  <table style="border-collapse:collapse;margin-bottom:16px">
    <tr>
      <td style="padding:4px 16px 4px 0"><span style="color:#16a34a">🟢 Bullish</span></td>
      <td style="padding:4px 16px 4px 0"><strong>{summary.bullish_count}</strong></td>
      <td style="padding:4px 16px 4px 0"><span style="color:#dc2626">🔴 Bearish</span></td>
      <td style="padding:4px 16px 4px 0"><strong>{summary.bearish_count}</strong></td>
      <td style="padding:4px 16px 4px 0"><span style="color:#6b7280">⚪ Neutral</span></td>
      <td><strong>{summary.neutral_count}</strong></td>
    </tr>
  </table>
  <h3>Market Outlook</h3>
  <p style="background:#f3f4f6;padding:12px;border-radius:6px">{summary.market_outlook}</p>
  {top_mover_html}
  <h3>Top Stories</h3>
  <table style="width:100%;border-collapse:collapse">
    <thead>
      <tr style="background:#1d4ed8;color:white">
        <th style="padding:8px 10px;text-align:left">Title</th>
        <th style="padding:8px 10px;text-align:left">Source</th>
        <th style="padding:8px 10px;text-align:left">Sentiment</th>
        <th style="padding:8px 10px;text-align:left">Confidence</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="color:#9ca3af;font-size:12px;margin-top:24px">Generated by Finax · {date_str}</p>
</body>
</html>"""

    return plain, html


# ---------------------------------------------------------------------------
# Delivery helpers
# ---------------------------------------------------------------------------


async def send_telegram(message: str) -> None:
    """Send a MarkdownV2 message to the configured Telegram chat."""
    token = settings.telegram_bot_token.get_secret_value()
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    logger.info("Telegram message sent successfully.")


async def send_email(subject: str, plain: str, html: str) -> None:
    """Send a multipart email via SMTP STARTTLS."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(settings.email_to)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password.get_secret_value(),
        start_tls=True,
    )
    logger.info("Email sent to: %s", ", ".join(settings.email_to))


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------


async def alert_node(state: FinaxState) -> dict:
    """LangGraph node: format and dispatch Telegram + email alerts."""
    analyzed = state["analyzed_articles"]
    summary = state["sentiment_summary"]

    if not analyzed or summary is None:
        logger.info("Alert: nothing to send, skipping.")
        return {}

    run_ts = state["run_timestamp"]
    date_str = run_ts.strftime("%Y-%m-%d")

    telegram_msg = _format_telegram(summary, analyzed, run_ts)
    plain, html = _format_email(summary, analyzed, run_ts)
    subject = f"Finax Daily Digest — {date_str}"

    results = await asyncio.gather(
        send_telegram(telegram_msg),
        send_email(subject, plain, html),
        return_exceptions=True,
    )

    for label, result in zip(("Telegram", "Email"), results):
        if isinstance(result, Exception):
            logger.error("%s delivery failed: %s", label, result)

    return {}
