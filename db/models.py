from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Edit(Base):
    __tablename__ = "edits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wiki = Column(String(32), index=True, nullable=False)
    title = Column(String(512), index=True, nullable=False)
    namespace = Column(Integer, nullable=False, default=0)
    edit_type = Column(String(16), nullable=False)
    user = Column(String(256), nullable=True)
    is_bot = Column(Boolean, default=False)
    is_minor = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)
    comment = Column(Text, default="")
    comment_length = Column(Integer, default=0)
    length_old = Column(Integer, default=0)
    length_new = Column(Integer, default=0)
    edit_size_delta = Column(Integer, default=0)
    revision_old = Column(Integer, nullable=True)
    revision_new = Column(Integer, nullable=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    ingested_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    vandalism_score = Column(Float, nullable=True)
    local_vandalism_score = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_edits_wiki_timestamp", "wiki", "timestamp"),
        Index("ix_edits_title_timestamp", "title", "timestamp"),
    )

    def __repr__(self):
        return f"<Edit(id={self.id}, title='{self.title}', wiki='{self.wiki}')>"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(32), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, default="")
    score = Column(Float, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    revision_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', title='{self.title}')>"
