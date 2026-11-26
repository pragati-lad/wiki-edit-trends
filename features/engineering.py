import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from db.models import Edit

FEATURE_COLUMNS = [
    "edit_size_delta",
    "abs_edit_size_delta",
    "length_old",
    "length_new",
    "comment_length",
    "is_bot",
    "is_anonymous",
    "is_minor",
    "namespace",
    "hour_of_day",
    "day_of_week",
    "size_ratio",
    "is_large_deletion",
    "is_new_page",
    "has_comment",
]


def extract_features_from_edit(edit: Edit) -> dict:
    """Extract ML features from a single Edit object."""
    length_old = edit.length_old or 0
    length_new = edit.length_new or 0
    delta = edit.edit_size_delta or 0
    comment_length = edit.comment_length or 0

    # Size ratio: how much of the page changed
    size_ratio = abs(delta) / max(length_old, 1)

    return {
        "edit_size_delta": delta,
        "abs_edit_size_delta": abs(delta),
        "length_old": length_old,
        "length_new": length_new,
        "comment_length": comment_length,
        "is_bot": int(edit.is_bot or False),
        "is_anonymous": int(edit.is_anonymous or False),
        "is_minor": int(edit.is_minor or False),
        "namespace": edit.namespace or 0,
        "hour_of_day": edit.timestamp.hour if edit.timestamp else 0,
        "day_of_week": edit.timestamp.weekday() if edit.timestamp else 0,
        "size_ratio": size_ratio,
        "is_large_deletion": int(delta < -500),
        "is_new_page": int(length_old == 0),
        "has_comment": int(comment_length > 0),
    }


def build_feature_matrix(
    session: Session,
    wiki: str = "enwiki",
    labeled_only: bool = True,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """Build a feature matrix from edits in the database.

    Returns (X, y) where X is the feature DataFrame and y is the
    vandalism_score series (or None if labeled_only=False).
    """
    query = session.query(Edit).filter(Edit.wiki == wiki)
    if labeled_only:
        query = query.filter(Edit.vandalism_score.isnot(None))

    edits = query.all()
    if not edits:
        return pd.DataFrame(columns=FEATURE_COLUMNS), None

    rows = [extract_features_from_edit(e) for e in edits]
    X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)

    y = None
    if labeled_only:
        # Convert continuous score to binary label: >0.5 = vandalism
        y = pd.Series(
            [1 if (e.vandalism_score or 0) > 0.5 else 0 for e in edits],
            name="is_vandalism",
        )

    return X, y
