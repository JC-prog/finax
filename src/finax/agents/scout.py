"""Scout Agent — fetches and filters financial news from NewsData.io."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from finax.config import settings
from finax.state import FinaxState, NewsArticle

logger = logging.getLogger(__name__)

NEWSDATA_BASE = "https://newsdata.io/api/1"
MAX_PAGES = 3  # 3 credits/day on free tier (200 credits/day limit)


async def _fetch_page(
    client: httpx.AsyncClient,
    api_key: str,
    query: str,
    next_page: str | None = None,
) -> tuple[list[dict], str | None]:
    """
    Fetch one page of news from NewsData.io /news endpoint.
    Returns (results, next_page_token).
    Handles 429 rate-limit by reading Retry-After and retrying once.
    """
    params: dict[str, str] = {
        "apikey": api_key,
        "q": query,
        "language": "en",
        "category": "business,technology",
    }
    if next_page:
        params["page"] = next_page

    for attempt in range(2):
        response = await client.get(f"{NEWSDATA_BASE}/news", params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            if attempt == 0:
                logger.warning("Rate-limited by NewsData.io. Waiting %ds...", retry_after)
                await asyncio.sleep(retry_after)
                continue
            else:
                response.raise_for_status()

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            logger.error("NewsData.io returned non-success status: %s", data)
            return [], None

        return data.get("results", []), data.get("nextPage")

    return [], None


def _parse_article(raw: dict) -> NewsArticle | None:
    """Map a NewsData.io result dict to a NewsArticle. Returns None on missing fields."""
    try:
        article_id = raw.get("article_id", "")
        title = raw.get("title", "")
        link = raw.get("link", "")

        if not all([article_id, title, link]):
            return None

        pub_date_str = raw.get("pubDate", "")
        try:
            published_at = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            published_at = datetime.now(timezone.utc)

        return NewsArticle(
            article_id=article_id,
            title=title,
            description=raw.get("description"),
            url=link,  # type: ignore[arg-type]
            source_name=raw.get("source_id", "unknown"),
            published_at=published_at,
            tickers=[],  # not available on free tier
            keywords=raw.get("keywords") or [],
        )
    except Exception as exc:
        logger.debug("Failed to parse article: %s — %s", raw.get("article_id"), exc)
        return None


def _filter_articles(
    articles: list[NewsArticle],
    tickers: list[str],
    keywords: list[str],
) -> list[NewsArticle]:
    """Keep articles whose title/description contains at least one ticker or keyword."""
    terms = [t.lower() for t in tickers + keywords]
    seen: set[str] = set()
    filtered: list[NewsArticle] = []

    for article in articles:
        if article.article_id in seen:
            continue
        haystack = f"{article.title} {article.description or ''}".lower()
        if any(term in haystack for term in terms):
            seen.add(article.article_id)
            filtered.append(article)

    return filtered


async def scout_node(state: FinaxState) -> dict:
    """LangGraph node: fetch and filter financial news from NewsData.io."""
    api_key = settings.newsdata_api_key.get_secret_value()
    query = " OR ".join(settings.watch_tickers + settings.watch_keywords)

    articles: list[NewsArticle] = []
    next_page: str | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        for page_num in range(MAX_PAGES):
            try:
                raw_results, next_page = await _fetch_page(client, api_key, query, next_page)
            except httpx.HTTPStatusError as exc:
                logger.error("NewsData.io HTTP error on page %d: %s", page_num + 1, exc)
                break
            except httpx.RequestError as exc:
                logger.error("NewsData.io request error on page %d: %s", page_num + 1, exc)
                break

            for raw in raw_results:
                article = _parse_article(raw)
                if article:
                    articles.append(article)

            logger.info("Scout page %d: fetched %d raw results", page_num + 1, len(raw_results))

            if not next_page:
                break

    filtered = _filter_articles(articles, settings.watch_tickers, settings.watch_keywords)
    logger.info(
        "Scout complete: %d articles fetched, %d after filtering", len(articles), len(filtered)
    )

    return {
        "news_articles": filtered,
        "run_timestamp": datetime.now(timezone.utc),
    }
