import re
from datetime import datetime, timezone

from db.models import Edit

_IP_V4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_IP_V6_RE = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")


def is_anonymous(user: str) -> bool:
    if not user:
        return False
    return bool(_IP_V4_RE.match(user) or _IP_V6_RE.match(user))


def parse_event(data: dict) -> Edit | None:
    """Parse a raw SSE JSON event into an Edit ORM object.

    Returns None if the event is missing required fields or is not
    an edit/new/log type we care about.
    """
    event_type = data.get("type")
    if event_type not in ("edit", "new", "log"):
        return None

    wiki = data.get("wiki")
    title = data.get("title")
    if not wiki or not title:
        return None

    meta = data.get("meta", {})
    dt_str = meta.get("dt")
    if not dt_str:
        return None

    try:
        timestamp = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None

    user = data.get("user", "")
    comment = data.get("comment", "")
    length = data.get("length", {})
    length_old = length.get("old") or 0
    length_new = length.get("new") or 0
    revision = data.get("revision", {})

    return Edit(
        wiki=wiki,
        title=title,
        namespace=data.get("namespace", 0),
        edit_type=event_type,
        user=user,
        is_bot=data.get("bot", False),
        is_minor=data.get("minor", False),
        is_anonymous=is_anonymous(user),
        comment=comment,
        comment_length=len(comment),
        length_old=length_old,
        length_new=length_new,
        edit_size_delta=length_new - length_old,
        revision_old=revision.get("old"),
        revision_new=revision.get("new"),
        timestamp=timestamp,
        ingested_at=datetime.now(timezone.utc),
    )
