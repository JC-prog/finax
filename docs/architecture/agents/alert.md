# Alert Agent

**File:** `src/finax/agents/alert.py`

The Alert Agent is the final node in the pipeline. It formats the analysis results and delivers them to Telegram and email simultaneously.

---

## Responsibilities

- Format the top 5 articles and market outlook for Telegram (MarkdownV2)
- Format the top 10 articles and a sentiment table for email (multipart HTML + plain text)
- Send both notifications concurrently via `asyncio.gather()`
- Escape all dynamic content for Telegram's MarkdownV2 to prevent formatting errors
- Record delivery status strings in `pending_alerts` for logging

---

## Telegram format

```
📊 *Finax Daily Digest* — 2026-03-18

*Market Outlook*
Sentiment is cautiously bullish driven by strong earnings reports...

*Top Stories*
1. [AAPL beats Q1 estimates](https://...)
   🟢 Bullish · 0.92 · Strong revenue growth exceeded analyst expectations

...

📈 Bullish: 6  📉 Bearish: 2  ➡️ Neutral: 3
🔥 Top movers: AAPL, NVDA, TSLA
```

- Limited to top **5** articles to stay within Telegram's 4096-character message limit
- All special characters (`_`, `*`, `[`, `]`, etc.) are escaped per the MarkdownV2 spec
- Long text fields are truncated with an ellipsis before escaping

---

## Email format

- **Subject:** `Finax Daily Digest — 2026-03-18`
- **Plain text:** newline-delimited summary for non-HTML clients
- **HTML:** styled table with article title, sentiment badge, confidence score, and reasoning
- Shows top **10** articles
- Sent via SMTP STARTTLS using `aiosmtplib`

---

## Concurrency

Both the Telegram and email sends are awaited concurrently:

```python
await asyncio.gather(send_telegram(...), send_email(...))
```

Failure of one channel is caught and logged independently so the other delivery still completes.
