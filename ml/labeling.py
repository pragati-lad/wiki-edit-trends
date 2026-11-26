from loguru import logger
from sqlalchemy.orm import Session

from db.models import Edit
from ingestion.enrichment import get_damaging_score

import time


def label_unlabeled_edits(
    session: Session,
    wiki: str = "enwiki",
    batch_size: int = 100,
    delay: float = 1.0,
) -> int:
    """Label edits that don't have a vandalism_score yet.

    Queries the Lift Wing API for each unlabeled edit and updates
    the vandalism_score column. Returns the number of edits labeled.
    """
    edits = (
        session.query(Edit)
        .filter(
            Edit.wiki == wiki,
            Edit.vandalism_score.is_(None),
            Edit.revision_new.isnot(None),
        )
        .limit(batch_size)
        .all()
    )

    labeled_count = 0
    for edit in edits:
        score = get_damaging_score(wiki, edit.revision_new)
        if score is not None:
            edit.vandalism_score = score
            labeled_count += 1
            logger.debug(f"Labeled rev {edit.revision_new}: {score:.4f}")
        else:
            logger.debug(f"Could not label rev {edit.revision_new}")

        time.sleep(delay)

    session.commit()
    logger.info(f"Labeled {labeled_count}/{len(edits)} edits from {wiki}")
    return labeled_count
