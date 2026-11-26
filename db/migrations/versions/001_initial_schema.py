"""Initial schema with edits and alerts tables.

Revision ID: 001
Revises: None
Create Date: 2024-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "edits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wiki", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("namespace", sa.Integer(), nullable=False),
        sa.Column("edit_type", sa.String(16), nullable=False),
        sa.Column("user", sa.String(256), nullable=True),
        sa.Column("is_bot", sa.Boolean(), default=False),
        sa.Column("is_minor", sa.Boolean(), default=False),
        sa.Column("is_anonymous", sa.Boolean(), default=False),
        sa.Column("comment", sa.Text(), default=""),
        sa.Column("comment_length", sa.Integer(), default=0),
        sa.Column("length_old", sa.Integer(), default=0),
        sa.Column("length_new", sa.Integer(), default=0),
        sa.Column("edit_size_delta", sa.Integer(), default=0),
        sa.Column("revision_old", sa.Integer(), nullable=True),
        sa.Column("revision_new", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.Column("vandalism_score", sa.Float(), nullable=True),
        sa.Column("local_vandalism_score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edits_wiki", "edits", ["wiki"])
    op.create_index("ix_edits_title", "edits", ["title"])
    op.create_index("ix_edits_timestamp", "edits", ["timestamp"])
    op.create_index("ix_edits_wiki_timestamp", "edits", ["wiki", "timestamp"])
    op.create_index("ix_edits_title_timestamp", "edits", ["title", "timestamp"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("edits")
