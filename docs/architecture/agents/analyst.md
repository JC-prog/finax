# Analyst Agent

**File:** `src/finax/agents/analyst.py`

The Analyst Agent is the second node in the pipeline. It sends each `NewsArticle` to Google Gemini 2.5 Flash and returns enriched `AnalyzedArticle` objects along with an aggregated `SentimentSummary`.

---

## Responsibilities

- Score each article as **bullish**, **bearish**, or **neutral** with a confidence value (0.0–1.0)
- Generate a one-sentence reasoning string per article
- Produce a market outlook summary paragraph across all articles
- Identify the top-moving tickers mentioned in the coverage
- Batch requests (5 articles per batch with 1 s delays) to respect Gemini's free-tier RPM limits
- Fall back to neutral sentiment if the LLM call fails for a given article

---

## Output models

```python
class AnalyzedArticle(BaseModel):
    # all fields from NewsArticle, plus:
    sentiment: Literal["bullish", "bearish", "neutral"]
    confidence: float          # 0.0 – 1.0
    reasoning: str             # one-sentence explanation

class SentimentSummary(BaseModel):
    bullish_count: int
    bearish_count: int
    neutral_count: int
    market_outlook: str        # paragraph summary
    top_movers: list[str]      # tickers most frequently mentioned
```

---

## Batching strategy

Gemini's free tier allows a limited number of requests per minute. The agent processes articles in batches of 5, inserting a 1-second sleep between batches. Requests within a batch are issued concurrently via `asyncio.gather()`.

---

## Conditional edge

If the Analyst receives an empty article list (shouldn't happen given the Scout conditional edge, but guarded defensively), the graph routes to `END` and skips the Alert node.
