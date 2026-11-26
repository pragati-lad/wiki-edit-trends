"""Train the vandalism XGBoost classifier.

Usage: python scripts/train_vandalism.py [--wiki enwiki]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from loguru import logger

from db.engine import SessionLocal
from features.engineering import build_feature_matrix
from ml.vandalism import VandalismClassifier

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")


def main():
    parser = argparse.ArgumentParser(description="Train vandalism classifier")
    parser.add_argument("--wiki", type=str, default="enwiki", help="Wiki to train on")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        logger.info(f"Building feature matrix for {args.wiki}...")
        X, y = build_feature_matrix(session, wiki=args.wiki, labeled_only=True)

        if X.empty or y is None:
            logger.error(
                "No labeled data found. Run label_with_liftwing.py first to "
                "generate silver labels via the Lift Wing API."
            )
            sys.exit(1)

        logger.info(f"Training data: {len(X)} samples, {y.sum()} positive ({y.mean():.1%} vandalism)")

        if y.sum() < 5 or (y == 0).sum() < 5:
            logger.error("Not enough samples in each class. Collect more labeled data.")
            sys.exit(1)

        clf = VandalismClassifier.train(X, y)
        clf.save()
        logger.info("Training complete.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
