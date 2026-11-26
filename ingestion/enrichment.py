import time

import requests
from loguru import logger

from config.settings import LIFTWING_URL


def get_damaging_score(wiki: str, revision_id: int) -> float | None:
    """Query the Lift Wing damaging model for a single revision.

    Returns the probability of the edit being damaging (0.0-1.0),
    or None if the request fails.
    """
    if not revision_id:
        return None

    payload = {"rev_id": revision_id}
    url = LIFTWING_URL

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"User-Agent": "WikiEditTrends/1.0 (educational project)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # Navigate the ORES-style response
        # Format: {wiki: {scores: {rev_id: {damaging: {score: {prediction, probability}}}}}}
        scores = data.get(wiki, {}).get("scores", {})
        rev_scores = scores.get(str(revision_id), {})
        damaging = rev_scores.get("damaging", {}).get("score", {})
        proba = damaging.get("probability", {})
        return proba.get("true")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Lift Wing API error for rev {revision_id}: {e}")
        return None
    except (KeyError, TypeError) as e:
        logger.warning(f"Unexpected Lift Wing response for rev {revision_id}: {e}")
        return None


def batch_label_edits(edits: list, wiki: str = "enwiki", delay: float = 1.0) -> dict:
    """Label a batch of edits with damaging scores.

    Returns a dict mapping revision_id -> score.
    Respects rate limiting with a delay between calls.
    """
    results = {}
    for edit in edits:
        rev_id = edit.revision_new
        if not rev_id:
            continue

        score = get_damaging_score(wiki, rev_id)
        if score is not None:
            results[rev_id] = score

        time.sleep(delay)

    return results
