"""
state.py
--------
Loads the cleaned tracker dataset once at process startup and holds it as a
module-level singleton, reading the same CSV the scheduled refresh job
writes and merging cached reason-tags via
reasons.tag_reasons_for_rows(max_articles=0) (cache-only, zero network
calls). No endpoint re-reads the CSV or re-tags reasons live; that only
happens in the scheduled refresh job (scripts/refresh_data.py).
"""

import pandas as pd

from .config import settings
from pipeline import reasons as reasons_module  # noqa: E402

_df: pd.DataFrame | None = None


def load_data() -> pd.DataFrame:
    global _df
    csv_path = settings.DATA_DIR / "cleaned" / "tracker_cleaned.csv"
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_localize(None)
    df = reasons_module.tag_reasons_for_rows(df, max_articles=0)
    _df = df
    return df


def get_data() -> pd.DataFrame:
    if _df is None:
        raise RuntimeError("Data not loaded yet -- load_data() must run at app startup (see main.py's lifespan).")
    return _df
