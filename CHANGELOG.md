# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-18

### Added

- **Scout Agent** — fetches and deduplicates financial news from NewsData.io with pagination support (up to 3 pages) and HTTP 429 backoff handling
- **Analyst Agent** — sentiment scoring (bullish / bearish / neutral) with confidence and one-sentence reasoning per article using Google Gemini 2.5 Flash; batched requests to respect free-tier RPM limits
- **Alert Agent** — multi-channel delivery via Telegram (MarkdownV2) and email (multipart HTML + plain text via SMTP)
- **LangGraph pipeline** — conditional `Scout → Analyst → Alert` graph wired in `graph.py`
- **APScheduler daemon** — daily cron trigger with configurable hour, minute, and timezone (default 06:00 SGT); 5-minute misfire grace window
- **Pydantic Settings** — lazy-loaded `.env` configuration with validation for all external credentials and watch-list parameters
- **Structured state** — `FinaxState` TypedDict with `NewsArticle`, `AnalyzedArticle`, and `SentimentSummary` models
- **Logging** — dual handlers writing to stdout and `finax.log`
- Initial project scaffold with `uv` build system, `ruff` linting, and `pytest-asyncio` test infrastructure

[Unreleased]: https://github.com/JC-Prog/finax/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JC-Prog/finax/releases/tag/v0.1.0
