import json
import time
from datetime import datetime, timedelta, timezone

import requests
import sseclient
from loguru import logger
from sqlalchemy import delete

from config.settings import (
    BACKOFF_FACTOR,
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    BATCH_SIZE,
    BATCH_TIMEOUT_SECONDS,
    RETENTION_DAYS,
    SSE_URL,
)
from db.engine import SessionLocal
from db.models import Alert, Edit
from ingestion.parser import parse_event


def _flush_batch(batch: list[Edit]) -> None:
    if not batch:
        return
    session = SessionLocal()
    try:
        session.add_all(batch)
        session.commit()
        logger.info(f"Flushed {len(batch)} edits to database")
    except Exception:
        session.rollback()
        logger.exception("Failed to flush batch")
    finally:
        session.close()


def _cleanup_old_edits() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    session = SessionLocal()
    try:
        result = session.execute(delete(Edit).where(Edit.timestamp < cutoff))
        deleted = result.rowcount
        session.execute(delete(Alert).where(Alert.created_at < cutoff))
        session.commit()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} edits older than {RETENTION_DAYS} days")
    except Exception:
        session.rollback()
        logger.exception("Cleanup failed")
    finally:
        session.close()


def _try_score_vandalism(edit: Edit) -> None:
    """Score edit with local vandalism model if available."""
    try:
        from ml.vandalism import VandalismClassifier

        clf = VandalismClassifier.load()
        edit.local_vandalism_score = clf.predict_single(edit)

        if edit.local_vandalism_score and edit.local_vandalism_score > 0.5:
            session = SessionLocal()
            try:
                alert = Alert(
                    alert_type="vandalism",
                    title=edit.title,
                    description=f"Potential vandalism detected (score: {edit.local_vandalism_score:.2f}) "
                    f"by user '{edit.user}' — delta: {edit.edit_size_delta}",
                    score=edit.local_vandalism_score,
                    revision_id=edit.revision_new,
                )
                session.add(alert)
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
    except (FileNotFoundError, ImportError):
        pass


def run_consumer(
    score_vandalism: bool = True,
    detect_breaking_news: bool = True,
) -> None:
    """Main consumer loop: connect to SSE, parse, batch-insert."""
    backoff = BACKOFF_INITIAL
    last_timestamp: str | None = None
    last_cleanup = time.time()
    cleanup_interval = 3600  # run cleanup every hour
    last_breaking_news_check = time.time()
    breaking_news_interval = 60  # check every minute

    while True:
        try:
            url = SSE_URL
            if last_timestamp:
                url = f"{SSE_URL}?since={last_timestamp}"

            logger.info(f"Connecting to SSE stream: {url}")
            response = requests.get(url, stream=True, timeout=300, headers={
                "User-Agent": "WikiEditTrends/1.0 (educational project)"
            })
            response.raise_for_status()

            client = sseclient.SSEClient(response)
            batch: list[Edit] = []
            batch_start = time.time()
            backoff = BACKOFF_INITIAL  # reset on successful connection

            for event in client.events():
                if event.event != "message":
                    continue

                try:
                    data = json.loads(event.data)
                except json.JSONDecodeError:
                    continue

                edit = parse_event(data)
                if edit is None:
                    continue

                # Track last timestamp for reconnection
                # Wikipedia expects ISO format with Z suffix, no +00:00
                ts = edit.timestamp.replace(tzinfo=None)
                last_timestamp = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

                if score_vandalism:
                    _try_score_vandalism(edit)

                batch.append(edit)

                # Flush when batch is full or timeout reached
                elapsed = time.time() - batch_start
                if len(batch) >= BATCH_SIZE or elapsed >= BATCH_TIMEOUT_SECONDS:
                    _flush_batch(batch)
                    batch = []
                    batch_start = time.time()

                # Periodic cleanup
                if time.time() - last_cleanup > cleanup_interval:
                    _cleanup_old_edits()
                    last_cleanup = time.time()

                # Periodic breaking news detection
                if (
                    detect_breaking_news
                    and time.time() - last_breaking_news_check > breaking_news_interval
                ):
                    _try_detect_breaking_news()
                    last_breaking_news_check = time.time()

        except requests.exceptions.RequestException as e:
            # Flush any remaining events before reconnecting
            _flush_batch(batch)
            batch = []

            # If we get a 400, the ?since= timestamp is invalid — drop it
            if "400" in str(e):
                logger.warning(f"Bad ?since= timestamp, resetting to live stream")
                last_timestamp = None
                backoff = BACKOFF_INITIAL

            logger.warning(f"SSE connection error: {e}. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * BACKOFF_FACTOR, BACKOFF_MAX)

        except KeyboardInterrupt:
            _flush_batch(batch)
            logger.info("Consumer stopped by user")
            break

        except Exception:
            _flush_batch(batch)
            batch = []
            logger.exception(f"Unexpected error. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * BACKOFF_FACTOR, BACKOFF_MAX)


def _try_detect_breaking_news() -> None:
    """Run breaking news detection if module is available."""
    try:
        from ml.breaking_news import detect_breaking_news

        session = SessionLocal()
        try:
            alerts = detect_breaking_news(session)
            for alert in alerts:
                session.add(alert)
            if alerts:
                session.commit()
                logger.info(f"Created {len(alerts)} breaking news alerts")
        except Exception:
            session.rollback()
            logger.exception("Breaking news detection failed")
        finally:
            session.close()
    except ImportError:
        pass
