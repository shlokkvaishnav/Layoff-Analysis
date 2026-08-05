"""
config.py
---------
Backend settings + one-time sys.path setup so the backend can import the
existing scraper/pipeline packages from the repo root as a library, without
duplicating any of their logic. Every other backend module imports REPO_ROOT
or settings from here first, so the sys.path insert below always runs before
anything tries `from pipeline import ...`.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/app/config.py -> backend/app -> backend -> repo root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class Settings:
    DATA_DIR: Path = Path(os.environ.get("DATA_DIR", str(REPO_ROOT / "data")))
    FRONTEND_ORIGINS = [
        o.strip() for o in os.environ.get("FRONTEND_ORIGINS", "http://localhost:3000").split(",") if o.strip()
    ]


settings = Settings()
