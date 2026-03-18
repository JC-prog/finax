# Architecture Overview

Finax is built as a **LangGraph state machine** with three sequential agent nodes, scheduled by APScheduler.

---

## Pipeline

```
┌─────────────┐     articles?     ┌──────────────┐   analyzed?   ┌─────────────┐
│  Scout Node │ ───────────────► │ Analyst Node │ ────────────► │ Alert Node  │
└─────────────┘                  └──────────────┘               └─────────────┘
       │ none                           │ none                          │
       ▼                                ▼                               ▼
      END                              END                             END
```

Each edge is conditional: if a node produces no output, the graph short-circuits to `END` rather than running downstream nodes unnecessarily.

---

## State

All nodes share a single `FinaxState` TypedDict that is threaded through the graph:

```python
FinaxState = {
    "news_articles":      list[NewsArticle],
    "analyzed_articles":  list[AnalyzedArticle],
    "sentiment_summary":  SentimentSummary | None,
    "pending_alerts":     list[str],
    "run_timestamp":      datetime,
}
```

Nodes receive the full state and return a partial dict with only the keys they update. LangGraph merges these partials automatically.

---

## Component map

| Module | Responsibility |
|---|---|
| `main.py` | Entry point; configures logging; starts scheduler |
| `scheduler.py` | APScheduler daemon; cron trigger; runs pipeline in fresh event loop |
| `graph.py` | Builds and wires the LangGraph `StateGraph` |
| `state.py` | TypedDict and Pydantic model definitions |
| `config.py` | Pydantic Settings with lazy `.env` loading |
| `agents/scout.py` | NewsData.io fetching, filtering, deduplication |
| `agents/analyst.py` | Gemini LLM sentiment analysis |
| `agents/alert.py` | Telegram and email delivery |

---

## Technology choices

| Concern | Library | Reason |
|---|---|---|
| Agent orchestration | LangGraph | Explicit state machine; conditional edges; easy to extend |
| LLM | Google Gemini 2.5 Flash | Fast, free-tier friendly, strong reasoning |
| News source | NewsData.io | Ticker-filtered financial news with free tier |
| Scheduling | APScheduler | Lightweight in-process cron; no external broker needed |
| Async HTTP | httpx | Modern async client with retry/backoff support |
| Email | aiosmtplib | Async SMTP; integrates cleanly with asyncio pipeline |
| Settings | Pydantic Settings | Type-safe `.env` parsing with validation |
