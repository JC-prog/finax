# Scheduler

**File:** `src/finax/scheduler.py`

Finax uses [APScheduler](https://apscheduler.readthedocs.io/) to run the pipeline as a daily daemon.

---

## Setup

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

def create_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler()
    trigger = CronTrigger(
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        timezone=settings.schedule_timezone,
    )
    scheduler.add_job(
        run_pipeline,
        trigger=trigger,
        misfire_grace_time=300,   # 5 minutes
        coalesce=True,
    )
    return scheduler
```

---

## Event loop handling

APScheduler executes jobs in a thread pool. Because the pipeline is fully async, `run_pipeline()` creates a **fresh event loop** per execution:

```python
def run_pipeline():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_pipeline_async())
    finally:
        loop.close()
```

This avoids `RuntimeError: This event loop is already running` issues that arise when reusing a shared loop.

---

## Misfire behaviour

| Setting | Value | Effect |
|---|---|---|
| `misfire_grace_time` | 300 s | If the scheduler was down at trigger time, the job still fires if the machine comes back within 5 minutes |
| `coalesce` | `True` | Multiple missed runs are coalesced into a single execution |

---

## Logging

The scheduler logs to the root logger. On each run:

- **Success:** `Pipeline completed successfully in Xs`
- **Failure:** `Pipeline failed: <exception message>` (full traceback at DEBUG level)

Both stdout and `finax.log` receive all log output.
