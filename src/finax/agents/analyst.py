"""Analyst Agent — sentiment scoring and market summary via Gemini 2.5 Flash."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from finax.config import settings
from finax.state import AnalyzedArticle, FinaxState, NewsArticle, SentimentSummary

logger = logging.getLogger(__name__)

CHUNK_SIZE = 5    # articles per async batch
CHUNK_DELAY = 1.0  # seconds between chunks


# ---------------------------------------------------------------------------
# Structured output schema for per-article scoring
# ---------------------------------------------------------------------------


class ArticleScore(BaseModel):
    sentiment: str  # "bullish" | "bearish" | "neutral"
    confidence: float
    reasoning: str


class SummaryOutput(BaseModel):
    market_outlook: str
    top_movers: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.google_api_key.get_secret_value(),  # type: ignore[arg-type]
        temperature=0.2,
    )


SENTIMENT_PROMPT = """\
You are a financial analyst. Analyze the news article below and provide:
- sentiment: one of "bullish", "bearish", or "neutral"
- confidence: a float between 0.0 and 1.0
- reasoning: one concise sentence explaining your score

Article title: {title}
Article description: {description}
"""

SUMMARY_PROMPT = """\
You are a senior market strategist. Based on the {n} analyzed articles below, provide:
- market_outlook: a concise paragraph (3-5 sentences) summarizing the overall market outlook
- top_movers: a list of up to 3 ticker symbols with the strongest bullish or bearish signals

If no ticker symbols are mentioned, return an empty list for top_movers.

Analyzed articles (JSON):
{articles_json}
"""


async def _score_article(
    llm: ChatGoogleGenerativeAI,
    article: NewsArticle,
) -> AnalyzedArticle:
    """Score a single article for sentiment using Gemini structured output."""
    scoring_llm = llm.with_structured_output(ArticleScore)
    prompt = SENTIMENT_PROMPT.format(
        title=article.title,
        description=article.description or "(no description)",
    )
    try:
        result: ArticleScore = await scoring_llm.ainvoke(prompt)  # type: ignore[assignment]
        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, float(result.confidence)))
        sentiment = result.sentiment.lower()
        if sentiment not in ("bullish", "bearish", "neutral"):
            sentiment = "neutral"
        return AnalyzedArticle(
            article=article,
            sentiment=sentiment,
            confidence=confidence,
            reasoning=result.reasoning,
        )
    except Exception as exc:
        logger.warning("Failed to score article '%s': %s", article.title[:60], exc)
        return AnalyzedArticle(
            article=article,
            sentiment="neutral",
            confidence=0.0,
            reasoning="Scoring failed; defaulting to neutral.",
        )


async def _generate_summary(
    llm: ChatGoogleGenerativeAI,
    analyzed: list[AnalyzedArticle],
) -> SentimentSummary:
    """Generate a market summary from all analyzed articles."""
    bullish = sum(1 for a in analyzed if a.sentiment == "bullish")
    bearish = sum(1 for a in analyzed if a.sentiment == "bearish")
    neutral = len(analyzed) - bullish - bearish

    articles_payload = [
        {
            "title": a.article.title,
            "sentiment": a.sentiment,
            "confidence": round(a.confidence, 2),
            "reasoning": a.reasoning,
        }
        for a in analyzed
    ]

    summary_llm = llm.with_structured_output(SummaryOutput)
    prompt = SUMMARY_PROMPT.format(
        n=len(analyzed),
        articles_json=json.dumps(articles_payload, indent=2),
    )

    try:
        result: SummaryOutput = await summary_llm.ainvoke(prompt)  # type: ignore[assignment]
        return SentimentSummary(
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            market_outlook=result.market_outlook,
            top_movers=result.top_movers,
            generated_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error("Failed to generate market summary: %s", exc)
        return SentimentSummary(
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            market_outlook="Summary generation failed.",
            top_movers=[],
            generated_at=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------


async def analyst_node(state: FinaxState) -> dict:
    """LangGraph node: score each article and produce a sentiment summary."""
    articles = state["news_articles"]
    if not articles:
        logger.info("Analyst: no articles to analyze, skipping.")
        return {"analyzed_articles": [], "sentiment_summary": None}

    llm = _build_llm()
    analyzed: list[AnalyzedArticle] = []

    # Process in chunks to stay within free-tier RPM limits
    for i in range(0, len(articles), CHUNK_SIZE):
        chunk = articles[i : i + CHUNK_SIZE]
        results = await asyncio.gather(*[_score_article(llm, a) for a in chunk])
        analyzed.extend(results)
        logger.info(
            "Analyst: scored articles %d–%d of %d",
            i + 1,
            min(i + CHUNK_SIZE, len(articles)),
            len(articles),
        )
        if i + CHUNK_SIZE < len(articles):
            await asyncio.sleep(CHUNK_DELAY)

    summary = await _generate_summary(llm, analyzed)
    logger.info(
        "Analyst complete: bullish=%d bearish=%d neutral=%d",
        summary.bullish_count,
        summary.bearish_count,
        summary.neutral_count,
    )

    return {"analyzed_articles": analyzed, "sentiment_summary": summary}
