from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Edit


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def make_edit(**overrides) -> Edit:
    """Factory for creating Edit objects with sensible defaults."""
    defaults = {
        "wiki": "enwiki",
        "title": "Test Article",
        "namespace": 0,
        "edit_type": "edit",
        "user": "TestUser",
        "is_bot": False,
        "is_minor": False,
        "is_anonymous": False,
        "comment": "Test edit",
        "comment_length": 9,
        "length_old": 1000,
        "length_new": 1050,
        "edit_size_delta": 50,
        "revision_old": 100,
        "revision_new": 101,
        "timestamp": datetime.now(timezone.utc),
        "ingested_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return Edit(**defaults)


SAMPLE_SSE_EVENT = {
    "type": "edit",
    "wiki": "enwiki",
    "title": "Python (programming language)",
    "namespace": 0,
    "user": "ExampleUser",
    "bot": False,
    "minor": False,
    "comment": "Fixed typo in introduction",
    "length": {"old": 5000, "new": 5020},
    "revision": {"old": 12345, "new": 12346},
    "meta": {"dt": "2024-06-15T12:30:00Z"},
}

SAMPLE_SSE_EVENT_ANON = {
    **SAMPLE_SSE_EVENT,
    "user": "192.168.1.100",
    "comment": "",
    "length": {"old": 5000, "new": 3000},
}

SAMPLE_SSE_EVENT_BOT = {
    **SAMPLE_SSE_EVENT,
    "user": "ClueBot NG",
    "bot": True,
    "comment": "Reverting vandalism",
}
