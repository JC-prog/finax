from datetime import datetime
from typing_extensions import TypedDict

from pydantic import BaseModel, HttpUrl


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class NewsArticle(BaseModel):
    article_id: str
    title: str
    description: str | None = None
    url: HttpUrl
    source_name: str
    published_at: datetime
    tickers: list[str] = []
    keywords: list[str] = []


class AnalyzedArticle(BaseModel):
    article: NewsArticle
    sentiment: str  # "bullish" | "bearish" | "neutral"
    confidence: float  # 0.0–1.0
    reasoning: str  # one-sentence justification


class SentimentSummary(BaseModel):
    bullish_count: int
    bearish_count: int
    neutral_count: int
    market_outlook: str  # LLM-generated paragraph
    top_movers: list[str]  # tickers with strongest signal
    generated_at: datetime


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------


class FinaxState(TypedDict):
    news_articles: list[NewsArticle]
    analyzed_articles: list[AnalyzedArticle]
    sentiment_summary: SentimentSummary | None
    pending_alerts: list[str]
    run_timestamp: datetime
