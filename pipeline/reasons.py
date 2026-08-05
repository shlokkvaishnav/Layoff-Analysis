"""
reasons.py
----------
Elevates news_scraper's stated-reason keyword tagging from a decorative
sidebar list into a first-class, merged feature of the main tracker
dataset. Every tracker row already carries its own source article URL (the
'Source' column) -- reused directly here instead of a separate, much
sparser RSS-headline sample that has no guaranteed link back to a specific
company/row at all.

Fetching+tagging every row live on every call would be slow and hammer
article sites, so results are cached by source URL in a small CSV
(cache_path) and only a capped batch of not-yet-cached rows is processed
per call -- coverage compounds across repeated runs instead of refetching
everything each time.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

# Self-contained path setup so this works regardless of the caller's own
# import style (direct script run, `python -m pipeline.reasons`, or import
# from backend/app/state.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper.news_scraper import extract_article_text, tag_stated_reasons  # noqa: E402

try:
    from . import config
except ImportError:
    import config

log = config.get_logger(__name__)

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "cleaned" / "reason_tags_cache.csv"


def _load_cache(cache_path: Path) -> pd.DataFrame:
    if cache_path.exists():
        cache = pd.read_csv(cache_path)
        cache["reason_tags"] = cache["reason_tags"].apply(json.loads)
        return cache
    return pd.DataFrame(columns=["source_url", "reason_tags", "tagged_at"])


def _save_cache(cache: pd.DataFrame, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    out = cache.copy()
    out["reason_tags"] = out["reason_tags"].apply(json.dumps)
    out.to_csv(cache_path, index=False)


def tag_reasons_for_rows(df: pd.DataFrame, cache_path: Path = DEFAULT_CACHE_PATH,
                          source_col: str = "Source", max_articles: int = 50) -> pd.DataFrame:
    """
    Fetch+tag up to `max_articles` not-yet-cached article URLs from
    `df[source_col]` (most recent `date` first), merge the running cache of
    previously-tagged URLs onto every row, and return `df` with a new
    `reason_tags` column (empty list where a row has no source URL or
    hasn't been tagged yet).
    """
    df = df.copy()
    if source_col not in df.columns:
        df["reason_tags"] = [[] for _ in range(len(df))]
        return df

    cache = _load_cache(cache_path)
    cached_urls = set(cache["source_url"])

    candidates = df[[source_col, "date"]].dropna(subset=[source_col]).drop_duplicates(subset=[source_col])
    candidates = candidates.assign(_sort_date=pd.to_datetime(candidates["date"], errors="coerce"))
    candidates = candidates.sort_values("_sort_date", ascending=False)
    to_fetch = [u for u in candidates[source_col] if u not in cached_urls][:max_articles]

    new_rows = []
    for url in to_fetch:
        try:
            text = extract_article_text(url)
            tags = tag_stated_reasons(text)
        except Exception as e:
            log.warning("Failed to tag %s: %s", url, e)
            tags = []
        new_rows.append({
            "source_url": url,
            "reason_tags": tags,
            "tagged_at": datetime.now(timezone.utc).isoformat(),
        })

    if new_rows:
        cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
        _save_cache(cache, cache_path)
        log.info("Tagged %d new article(s); cache now covers %d URL(s).", len(new_rows), len(cache))

    tag_map = dict(zip(cache["source_url"], cache["reason_tags"]))
    df["reason_tags"] = df[source_col].map(tag_map)
    df["reason_tags"] = df["reason_tags"].apply(lambda v: v if isinstance(v, list) else [])
    return df


def summarize_reasons(df: pd.DataFrame, stage_col: str = "stage") -> dict:
    """
    Coverage + frequency summary of reason_tags -- a DELIVERABLE, not
    decoration, mirroring clean.py's _headcount_imputed transparency
    pattern: never present reason-tag frequencies without saying what
    fraction of rows they're actually based on.
    """
    empty_summary = {
        "coverage_pct": 0.0, "tagged_rows": 0, "total_rows": len(df),
        "overall_counts": {}, "by_stage_counts": {}, "by_quarter_counts": {},
    }
    if "reason_tags" not in df.columns:
        return empty_summary

    tagged_mask = df["reason_tags"].apply(lambda v: isinstance(v, list) and len(v) > 0)
    tagged_rows = int(tagged_mask.sum())
    total_rows = len(df)
    if tagged_rows == 0:
        return empty_summary

    cols = ["date", "reason_tags"] + ([stage_col] if stage_col in df.columns else [])
    exploded = df.loc[tagged_mask, cols].explode("reason_tags")

    overall_counts = exploded["reason_tags"].value_counts().to_dict()

    by_stage_counts = {}
    if stage_col in exploded.columns:
        by_stage_counts = exploded.groupby(stage_col)["reason_tags"].value_counts().to_dict()

    quarters = pd.to_datetime(exploded["date"], errors="coerce").dt.to_period("Q").astype(str)
    by_quarter_counts = exploded.assign(quarter=quarters).groupby("quarter")["reason_tags"].value_counts().to_dict()

    return {
        "coverage_pct": round(100 * tagged_rows / total_rows, 1) if total_rows else 0.0,
        "tagged_rows": tagged_rows,
        "total_rows": total_rows,
        "overall_counts": overall_counts,
        "by_stage_counts": by_stage_counts,
        "by_quarter_counts": by_quarter_counts,
    }


if __name__ == "__main__":
    clean_path = Path(__file__).resolve().parent.parent / "data" / "cleaned" / "tracker_cleaned.csv"
    if not clean_path.exists():
        log.error("Could not find %s -- run pipeline/clean.py first.", clean_path)
        sys.exit(1)

    tracker_df = pd.read_csv(clean_path)
    tracker_df = tag_reasons_for_rows(tracker_df, max_articles=20)

    summary = summarize_reasons(tracker_df)
    log.info(
        "Reason-tag coverage: %d/%d rows (%.1f%%)",
        summary["tagged_rows"], summary["total_rows"], summary["coverage_pct"],
    )
    log.info("Overall reason counts: %s", summary["overall_counts"])
