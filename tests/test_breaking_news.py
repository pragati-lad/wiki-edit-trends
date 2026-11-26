from datetime import datetime, timedelta, timezone

from db.models import Alert
from ml.breaking_news import detect_breaking_news
from tests.conftest import make_edit


class TestBreakingNewsDetection:
    def _insert_spike(self, session, title="Breaking Article", count=20, minutes_ago=5):
        """Insert a spike of edits for a single article."""
        base_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        for i in range(count):
            edit = make_edit(
                title=title,
                user=f"Editor_{i}",
                timestamp=base_time + timedelta(seconds=i * 10),
                namespace=0,
            )
            session.add(edit)
        session.commit()

    def _insert_background(self, session, title="Breaking Article", count=2, hours_ago=3):
        """Insert background-level edits in history."""
        base_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        for i in range(count):
            edit = make_edit(
                title=title,
                user=f"HistEditor_{i}",
                timestamp=base_time + timedelta(minutes=i * 30),
                namespace=0,
            )
            session.add(edit)
        session.commit()

    def test_detects_spike(self, session):
        # Add historical background noise (low rate)
        self._insert_background(session, count=2, hours_ago=3)
        self._insert_background(session, count=1, hours_ago=2)
        # Add a recent spike
        self._insert_spike(session, count=20, minutes_ago=5)

        alerts = detect_breaking_news(session)
        assert len(alerts) >= 1
        alert = alerts[0]
        assert alert.alert_type == "breaking_news"
        assert alert.title == "Breaking Article"
        assert alert.score >= 3.0

    def test_no_alert_for_low_activity(self, session):
        # Only 2 recent edits — below MIN_EDITS threshold
        self._insert_spike(session, count=2, minutes_ago=5)
        alerts = detect_breaking_news(session)
        assert len(alerts) == 0

    def test_no_alert_single_editor(self, session):
        """Spike from a single editor should not trigger."""
        base_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        for i in range(15):
            edit = make_edit(
                title="Single Editor Article",
                user="SameUser",  # all same user
                timestamp=base_time + timedelta(seconds=i * 10),
                namespace=0,
            )
            session.add(edit)
        session.commit()

        alerts = detect_breaking_news(session)
        # Should not trigger because unique editors < MIN_UNIQUE_EDITORS
        breaking_alerts = [a for a in alerts if a.title == "Single Editor Article"]
        assert len(breaking_alerts) == 0

    def test_cooldown_prevents_duplicate(self, session):
        self._insert_background(session, count=1, hours_ago=3)
        self._insert_spike(session, count=20, minutes_ago=5)

        # First detection
        alerts = detect_breaking_news(session)
        for alert in alerts:
            session.add(alert)
        session.commit()

        # Second detection should not re-alert
        alerts2 = detect_breaking_news(session)
        breaking = [a for a in alerts2 if a.title == "Breaking Article"]
        assert len(breaking) == 0

    def test_ignores_non_article_namespace(self, session):
        """Edits in talk namespace (1) should be ignored."""
        base_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        for i in range(15):
            edit = make_edit(
                title="Talk:Some Article",
                user=f"Editor_{i}",
                timestamp=base_time + timedelta(seconds=i * 10),
                namespace=1,
            )
            session.add(edit)
        session.commit()

        alerts = detect_breaking_news(session)
        assert len(alerts) == 0
