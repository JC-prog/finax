"""Finax entry point — starts the APScheduler daemon."""

import argparse
import logging
import sys
from pathlib import Path

from finax.config import settings
from finax.scheduler import create_scheduler, run_pipeline


def _configure_logging() -> None:
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "finax.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Finax financial intelligence daemon")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the pipeline once immediately and exit instead of starting the scheduler",
    )
    args = parser.parse_args()

    _configure_logging()

    if args.run_now:
        run_pipeline()
        return

    scheduler = create_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.getLogger(__name__).info("Finax scheduler stopped.")


if __name__ == "__main__":
    main()
