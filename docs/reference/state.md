# State & Models

**File:** `src/finax/state.py`

All data structures used in the LangGraph pipeline are defined here.

---

## FinaxState

The top-level state TypedDict threaded through every graph node.

```python
class FinaxState(TypedDict):
    news_articles:     list[NewsArticle]
    analyzed_articles: list[AnalyzedArticle]
    sentiment_summary: SentimentSummary | None
    pending_alerts:    list[str]
    run_timestamp:     datetime
```

| Field | Set by | Description |
|---|---|---|
| `news_articles` | Scout | Raw articles fetched from NewsData.io |
| `analyzed_articles` | Analyst | Articles enriched with sentiment scores |
| `sentiment_summary` | Analyst | Aggregated market outlook and counts |
| `pending_alerts` | Alert | Delivery status strings for logging |
| `run_timestamp` | Scheduler | UTC datetime when the pipeline was triggered |

---

## NewsArticle

```python
class NewsArticle(BaseModel):
    id:           str
    title:        str
    description:  str | None
    url:          str
    source:       str
    published_at: datetime
    tickers:      list[str]
    keywords:     list[str]
```

---

## AnalyzedArticle

Extends `NewsArticle` with sentiment fields added by the Analyst Agent.

```python
class AnalyzedArticle(BaseModel):
    # inherits all NewsArticle fields
    sentiment:  Literal["bullish", "bearish", "neutral"]
    confidence: float   # 0.0 – 1.0
    reasoning:  str     # one-sentence LLM explanation
```

---

## SentimentSummary

Aggregated output produced by the Analyst Agent after all articles are scored.

```python
class SentimentSummary(BaseModel):
    bullish_count:  int
    bearish_count:  int
    neutral_count:  int
    market_outlook: str        # paragraph market summary
    top_movers:     list[str]  # most-mentioned tickers
```
