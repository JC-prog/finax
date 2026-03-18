# Scout Agent

**File:** `src/finax/agents/scout.py`

The Scout Agent is the first node in the pipeline. It fetches recent financial news from [NewsData.io](https://newsdata.io/) and produces a deduplicated list of `NewsArticle` objects for the Analyst Agent.

---

## Responsibilities

- Query NewsData.io for articles matching `WATCH_TICKERS` and `WATCH_KEYWORDS`
- Paginate through results (up to 3 pages) to stay within the free-tier request budget
- Handle HTTP 429 rate-limit responses by honoring `Retry-After` headers
- Deduplicate articles by ID across pages
- Return a `list[NewsArticle]` in the pipeline state

---

## Output model

```python
class NewsArticle(BaseModel):
    id: str
    title: str
    description: str | None
    url: str
    source: str
    published_at: datetime
    tickers: list[str]
    keywords: list[str]
```

---

## Rate-limiting behaviour

NewsData.io's free tier enforces request-per-minute limits. The Scout Agent:

1. Detects a `429` response and reads the `Retry-After` header
2. Sleeps for the indicated duration before retrying
3. Stops paginating after 3 pages to avoid exhausting the daily quota

---

## Conditional edge

If the Scout returns zero articles (e.g. no news today, API unavailable), the graph routes directly to `END` and skips the Analyst and Alert nodes.
