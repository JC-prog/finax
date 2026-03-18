# Finax

**Autonomous multi-agent financial intelligence system for real-time market monitoring and sentiment analysis.**

Finax runs as a daily scheduled daemon. It fetches financial news for a configured watch list, scores each article with an LLM, and delivers a formatted digest to Telegram and email.

---

## How it works

```
Scout Agent  →  Analyst Agent  →  Alert Agent
```

1. **Scout** — polls NewsData.io for the latest articles matching your tickers and keywords
2. **Analyst** — sends each article to Google Gemini 2.5 Flash for sentiment scoring and market outlook generation
3. **Alert** — formats and delivers the digest to Telegram and email

The pipeline is orchestrated with [LangGraph](https://github.com/langchain-ai/langgraph) and triggered daily via [APScheduler](https://apscheduler.readthedocs.io/).

---

## Quick start

```bash
git clone https://github.com/JC-Prog/finax.git
cd finax
uv sync
cp .env.example .env   # fill in your API keys
uv run finax
```

See [Installation](getting-started/installation.md) and [Configuration](getting-started/configuration.md) for full setup instructions.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.12 |
| uv | latest |

External services required:

- [Google AI Studio](https://aistudio.google.com/) — Gemini API key
- [NewsData.io](https://newsdata.io/) — news API key
- Telegram bot (via [@BotFather](https://t.me/BotFather))
- SMTP server (Gmail recommended)
