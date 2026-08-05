"""
reasons_service.py
--------------------
Thin wrapper around pipeline.reasons -- reshapes its tuple-keyed groupby
output into flat JSON-friendly lists; the counting/coverage logic itself is
untouched (see pipeline/reasons.py::summarize_reasons).
"""

import pandas as pd

from pipeline import reasons as reasons_module  # noqa: E402


def summary(df: pd.DataFrame) -> dict:
    s = reasons_module.summarize_reasons(df)
    return {"coverage_pct": s["coverage_pct"], "tagged_rows": s["tagged_rows"], "total_rows": s["total_rows"]}


def frequency(df: pd.DataFrame) -> dict:
    s = reasons_module.summarize_reasons(df)
    counts = [{"reason": k, "count": v} for k, v in s["overall_counts"].items()]
    counts.sort(key=lambda c: c["count"], reverse=True)
    return {"coverage_pct": s["coverage_pct"], "counts": counts}


def by_stage(df: pd.DataFrame) -> list[dict]:
    s = reasons_module.summarize_reasons(df)
    # keys are (stage, reason) tuples, from groupby(stage)["reason_tags"].value_counts()
    return [{"stage": k[0], "reason": k[1], "count": v} for k, v in s["by_stage_counts"].items()]


def over_time(df: pd.DataFrame) -> list[dict]:
    s = reasons_module.summarize_reasons(df)
    # keys are (quarter, reason) tuples
    return [{"quarter": k[0], "reason": k[1], "count": v} for k, v in s["by_quarter_counts"].items()]
