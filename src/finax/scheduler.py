"""APScheduler setup — runs the Finax pipeline daily at 06:00 SGT."""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from finax.config import settings
from finax.graph import build_graph

logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """
    Synchronous wrapper invoked by APScheduler.
    Creates a fresh asyncio event loop per run to avoid loop-reuse issues
    with LangGraph's internal async machinery.
    Builds the graph inside the function so settings are loaded at runtime.
    """
    graph = build_graph()
    initial_state = {
        "news_articles": [],
        "analyzed_articles": [],
        "sentiment_summary": None,
        "pending_alerts": [],
        "run_timestamp": datetime.now(timezone.utc),
    }
    logger.info("Starting Finax pipeline run at %s", datetime.now(timezone.utc).isoformat())
    try:
        asyncio.run(graph.ainvoke(initial_state))
        logger.info("Pipeline completed successfully.")
    except Exception:
        logger.exception("Pipeline run failed.")


def create_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=settings.schedule_timezone)
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(
            hour=settings.schedule_hour,
            minute=settings.schedule_minute,
            timezone=settings.schedule_timezone,
        ),
        id="finax_daily",
        name="Finax daily financial news pipeline",
        misfire_grace_time=300,  # tolerate up to 5 minutes of startup delay
        coalesce=True,  # skip extra runs if multiple misfired
    )
    logger.info(
        "Scheduler configured: daily at %02d:%02d %s",
        settings.schedule_hour,
        settings.schedule_minute,
        settings.schedule_timezone,
    )
    return scheduler
