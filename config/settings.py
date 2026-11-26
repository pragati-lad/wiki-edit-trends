import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'wiki_edits.db'}").replace("postgres://", "postgresql://", 1)

SSE_URL = os.getenv(
    "SSE_URL", "https://stream.wikimedia.org/v2/stream/recentchange"
)

LIFTWING_URL = os.getenv(
    "LIFTWING_URL",
    "https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-damaging:predict",
)

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
BATCH_TIMEOUT_SECONDS = int(os.getenv("BATCH_TIMEOUT_SECONDS", "10"))

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))

# Reconnection backoff
BACKOFF_INITIAL = 1
BACKOFF_MAX = 60
BACKOFF_FACTOR = 2
