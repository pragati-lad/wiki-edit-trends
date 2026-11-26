"""Single entry point: starts both the consumer and dashboard together."""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
PORT = 8501


def main():
    os.chdir(ROOT)

    # Ensure tables exist
    print("Creating database tables...")
    subprocess.run([str(VENV_PYTHON), "-c",
        "from db.engine import engine; from db.models import Base; Base.metadata.create_all(bind=engine)"
    ], check=True)

    print("Starting consumer (background)...")
    consumer = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "ingestion"],
        cwd=str(ROOT),
    )

    print("Starting dashboard on port", PORT, "...")
    dashboard = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "streamlit", "run", "dashboard/app.py",
         "--server.port", str(PORT),
         "--server.headless", "true"],
        cwd=str(ROOT),
    )

    # Give streamlit a moment to start, then open browser
    time.sleep(3)
    url = f"http://localhost:{PORT}"
    print(f"\nOpening {url} in your browser...")
    webbrowser.open(url)

    print("Both running! Press Ctrl+C to stop everything.\n")

    try:
        dashboard.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...")
        consumer.terminate()
        dashboard.terminate()
        consumer.wait()
        dashboard.wait()
        print("Done.")


if __name__ == "__main__":
    main()
