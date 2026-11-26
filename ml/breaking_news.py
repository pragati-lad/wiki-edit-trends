from datetime import datetime, timedelta, timezone

import numpy as np
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import Alert, Edit

# Thresholds
Z_SCORE_THRESHOLD = 3.0
MIN_EDITS = 5
MIN_UNIQUE_EDITORS = 3
WINDOW_MINUTES = 30
LOOKBACK_HOURS = 6
COOLDOWN_MINUTES = 60  # don't re-alert for the same article within this window


def detect_breaking_news(session: Session) -> list[Alert]:
    """Detect articles with anomalous edit velocity using z-score.

    Compares the edit count in the recent window against the historical
    mean/std for each article. Returns Alert objects for flagged articles.
    """
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    lookback_cutoff = now - timedelta(hours=LOOKBACK_HOURS)

    # Get articles with activity in the recent window
    recent_stats = (
        session.query(
            Edit.title,
            func.count().label("recent_count"),
            func.count(func.distinct(Edit.user)).label("unique_editors"),
        )
        .filter(
            Edit.timestamp >= recent_cutoff,
            Edit.namespace == 0,  # only main articles
        )
        .group_by(Edit.title)
        .having(func.count() >= MIN_EDITS)
        .all()
    )

    if not recent_stats:
        return []

    alerts = []

    for title, recent_count, unique_editors in recent_stats:
        if unique_editors < MIN_UNIQUE_EDITORS:
            continue

        # Check cooldown: skip if we already alerted recently
        existing_alert = (
            session.query(Alert)
            .filter(
                Alert.alert_type == "breaking_news",
                Alert.title == title,
                Alert.created_at >= now - timedelta(minutes=COOLDOWN_MINUTES),
            )
            .first()
        )
        if existing_alert:
            continue

        # Get historical edit rate for this article (per WINDOW_MINUTES chunk)
        historical_counts = _get_historical_window_counts(
            session, title, lookback_cutoff, recent_cutoff
        )

        if len(historical_counts) < 2:
            # Not enough historical data; use a simple threshold
            if recent_count >= 10 and unique_editors >= MIN_UNIQUE_EDITORS:
                z_score = float(recent_count)  # treat count as z-score proxy
            else:
                continue
        else:
            mean = np.mean(historical_counts)
            std = np.std(historical_counts)
            if std == 0:
                z_score = float(recent_count - mean) if recent_count > mean else 0.0
            else:
                z_score = (recent_count - mean) / std

        if z_score >= Z_SCORE_THRESHOLD:
            alert = Alert(
                alert_type="breaking_news",
                title=title,
                description=(
                    f"Edit spike detected: {recent_count} edits in the last "
                    f"{WINDOW_MINUTES} min by {unique_editors} editors "
                    f"(z-score: {z_score:.1f})"
                ),
                score=z_score,
            )
            alerts.append(alert)
            logger.info(f"Breaking news detected: '{title}' (z={z_score:.1f})")

    return alerts


def _get_historical_window_counts(
    session: Session,
    title: str,
    start: datetime,
    end: datetime,
) -> list[int]:
    """Get edit counts per WINDOW_MINUTES chunk for an article."""
    edits = (
        session.query(Edit.timestamp)
        .filter(
            Edit.title == title,
            Edit.timestamp >= start,
            Edit.timestamp < end,
        )
        .all()
    )

    if not edits:
        return []

    # Bucket edits into WINDOW_MINUTES-sized chunks
    counts = {}
    for (ts,) in edits:
        # Normalize tz: SQLite returns naive datetimes, PostgreSQL returns aware
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        bucket = int((ts - start).total_seconds() // (WINDOW_MINUTES * 60))
        counts[bucket] = counts.get(bucket, 0) + 1

    # Fill in empty buckets with 0
    total_buckets = int((end - start).total_seconds() // (WINDOW_MINUTES * 60))
    return [counts.get(i, 0) for i in range(total_buckets)]
