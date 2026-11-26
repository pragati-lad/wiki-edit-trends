"""Batch-label edits using the Lift Wing damaging API.

Usage: python scripts/label_with_liftwing.py [--batch-size 100] [--wiki enwiki]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from loguru import logger

from db.engine import SessionLocal
from ml.labeling import label_unlabeled_edits

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")


def main():
    parser = argparse.ArgumentParser(description="Label edits with Lift Wing API")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of edits to label")
    parser.add_argument("--wiki", type=str, default="enwiki", help="Wiki to label")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        total_labeled = 0
        while True:
            labeled = label_unlabeled_edits(
                session,
                wiki=args.wiki,
                batch_size=args.batch_size,
                delay=args.delay,
            )
            total_labeled += labeled
            if labeled < args.batch_size:
                break
            logger.info(f"Progress: {total_labeled} edits labeled so far")

        logger.info(f"Done. Total edits labeled: {total_labeled}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
