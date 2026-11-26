"""Entry point: python -m ingestion"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from db.engine import engine
from db.models import Base
from ingestion.consumer import run_consumer

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")


def main():
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    logger.info("Starting Wikipedia edit consumer...")
    run_consumer()


if __name__ == "__main__":
    main()
else:
    main()
