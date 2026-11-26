from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from db.models import Alert, Edit


def recent_edits(session: Session, limit: int = 20, wiki: str = "enwiki") -> pd.DataFrame:
    """Fetch the most recent edits for the live feed (English Wikipedia only)."""
    rows = (
        session.query(
            Edit.timestamp,
            Edit.wiki,
            Edit.title,
            Edit.user,
            Edit.edit_size_delta,
            Edit.is_bot,
            Edit.is_anonymous,
            Edit.is_minor,
            Edit.comment,
        )
        .filter(Edit.wiki == wiki, Edit.namespace == 0)
        .order_by(Edit.timestamp.desc())
        .limit(limit)
        .all()
    )
    return pd.DataFrame(rows, columns=[
        "timestamp", "wiki", "title", "user", "edit_size_delta",
        "is_bot", "is_anonymous", "is_minor", "comment",
    ])


def edits_per_minute(session: Session, minutes: int = 30) -> pd.DataFrame:
    """Edits per minute for the last N minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # Use strftime for SQLite compatibility, extract for PostgreSQL
    try:
        rows = (
            session.query(
                func.strftime("%Y-%m-%d %H:%M", Edit.timestamp).label("minute"),
                func.count().label("count"),
            )
            .filter(Edit.timestamp >= cutoff)
            .group_by("minute")
            .order_by("minute")
            .all()
        )
    except Exception:
        rows = (
            session.query(
                func.date_trunc("minute", Edit.timestamp).label("minute"),
                func.count().label("count"),
            )
            .filter(Edit.timestamp >= cutoff)
            .group_by("minute")
            .order_by("minute")
            .all()
        )

    df = pd.DataFrame(rows, columns=["minute", "count"])
    if not df.empty:
        df["minute"] = pd.to_datetime(df["minute"])
    return df


def bot_human_counts(session: Session, minutes: int = 60) -> dict:
    """Bot vs Human edit counts in the last N minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    total = session.query(func.count()).filter(Edit.timestamp >= cutoff).scalar() or 0
    bots = (
        session.query(func.count())
        .filter(Edit.timestamp >= cutoff, Edit.is_bot.is_(True))
        .scalar()
        or 0
    )
    return {"bot": bots, "human": total - bots}


def trending_articles(session: Session, minutes: int = 30, limit: int = 10, wiki: str = "enwiki") -> pd.DataFrame:
    """Top articles by edit count in the last N minutes (English Wikipedia only)."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    rows = (
        session.query(
            Edit.title,
            func.count().label("edit_count"),
            func.count(func.distinct(Edit.user)).label("unique_editors"),
            func.sum(func.abs(Edit.edit_size_delta)).label("total_delta"),
        )
        .filter(
            Edit.timestamp >= cutoff,
            Edit.namespace == 0,
            Edit.wiki == wiki,
        )
        .group_by(Edit.title)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return pd.DataFrame(rows, columns=[
        "title", "edit_count", "unique_editors", "total_delta",
    ])


def edit_size_distribution(session: Session, minutes: int = 60) -> pd.DataFrame:
    """Edit size deltas for histogram."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    rows = (
        session.query(Edit.edit_size_delta)
        .filter(
            Edit.timestamp >= cutoff,
            Edit.edit_size_delta.between(-5000, 5000),
        )
        .all()
    )
    return pd.DataFrame(rows, columns=["edit_size_delta"])


def recent_alerts(session: Session, limit: int = 20) -> pd.DataFrame:
    """Fetch the most recent alerts."""
    rows = (
        session.query(
            Alert.created_at,
            Alert.alert_type,
            Alert.title,
            Alert.description,
            Alert.score,
        )
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    return pd.DataFrame(rows, columns=[
        "created_at", "alert_type", "title", "description", "score",
    ])


def total_edit_count(session: Session) -> int:
    return session.query(func.count()).select_from(Edit).scalar() or 0


def kpi_stats(session: Session, minutes: int = 10) -> dict:
    """Key metrics for the dashboard header."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    recent = session.query(func.count()).filter(Edit.timestamp >= cutoff).scalar() or 0
    edits_per_min = round(recent / max(minutes, 1), 1)

    anon_count = (
        session.query(func.count())
        .filter(Edit.timestamp >= cutoff, Edit.is_anonymous.is_(True))
        .scalar() or 0
    )
    anon_pct = round(100 * anon_count / max(recent, 1), 1)

    unique_articles = (
        session.query(func.count(func.distinct(Edit.title)))
        .filter(Edit.timestamp >= cutoff, Edit.namespace == 0)
        .scalar() or 0
    )

    unique_wikis = (
        session.query(func.count(func.distinct(Edit.wiki)))
        .filter(Edit.timestamp >= cutoff)
        .scalar() or 0
    )

    alert_count = (
        session.query(func.count())
        .select_from(Alert)
        .filter(Alert.created_at >= cutoff)
        .scalar() or 0
    )

    avg_delta = (
        session.query(func.avg(func.abs(Edit.edit_size_delta)))
        .filter(Edit.timestamp >= cutoff)
        .scalar()
    )
    avg_delta = round(avg_delta or 0, 0)

    return {
        "recent_edits": recent,
        "edits_per_min": edits_per_min,
        "anon_pct": anon_pct,
        "unique_articles": unique_articles,
        "unique_wikis": unique_wikis,
        "alert_count": alert_count,
        "avg_edit_size": int(avg_delta),
    }


def top_wikis_summary(session: Session, minutes: int = 10, limit: int = 5) -> list[tuple]:
    """Top wikis with counts for a quick summary."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return (
        session.query(Edit.wiki, func.count().label("count"))
        .filter(Edit.timestamp >= cutoff)
        .group_by(Edit.wiki)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )


def wiki_distribution(session: Session, minutes: int = 60, limit: int = 10) -> pd.DataFrame:
    """Top wikis by edit count."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    rows = (
        session.query(Edit.wiki, func.count().label("count"))
        .filter(Edit.timestamp >= cutoff)
        .group_by(Edit.wiki)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return pd.DataFrame(rows, columns=["wiki", "count"])
