"""Finax entry point — starts the APScheduler daemon."""

import logging
import sys

from finax.scheduler import create_scheduler


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("finax.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    _configure_logging()
    scheduler = create_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.getLogger(__name__).info("Finax scheduler stopped.")


if __name__ == "__main__":
    main()
