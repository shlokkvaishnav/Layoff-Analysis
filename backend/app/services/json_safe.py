"""
json_safe.py
------------
pandas NaN/NaT/pd.NA are not valid JSON tokens -- handing raw DataFrame
records to FastAPI's encoder either emits invalid JSON or crashes on pd.NA.
Every service function must pass its output through df_records_safe()
before building Pydantic models from it. This is a real, not theoretical,
pitfall here: WARN-Act-shaped rows lack stage/country/ai_flag/funds_raised_mm
entirely, so any endpoint touching the raw dataset WILL see nulls.
"""

import pandas as pd


def df_records_safe(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of JSON-safe dicts (NaN/NaT/pd.NA -> None)."""
    safe = df.astype(object).where(pd.notnull(df), None)
    return safe.to_dict("records")
