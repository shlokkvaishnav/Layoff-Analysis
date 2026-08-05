"""
refresh_data.py
----------------
Scheduled data-refresh entry point (see .github/workflows/refresh-data.yml).
Scrapes -> cleans -> tags a capped batch of reasons -> writes
data/cleaned/last_refresh.json.

This is the ONLY place that calls the slow, live-network parts of the
pipeline (tracker_scraper.get_live_tracker_data(), which can take up to
~300s via the Apify fallback; reasons.tag_reasons_for_rows() with a nonzero
max_articles, which does live per-article HTTP fetches). The backend API
never does either of these synchronously at request time -- see
backend/app/state.py, which only ever calls tag_reasons_for_rows with
max_articles=0 (cache-only, no network).

get_live_tracker_data() raises RuntimeError if every source fails -- that
exception is intentionally left uncaught here, so this script exits non-zero
and the calling workflow's commit step never runs, leaving the last
known-good data/*.csv untouched.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline import clean, reasons  # noqa: E402
from pipeline.config import get_logger  # noqa: E402
from scraper import tracker_scraper  # noqa: E402
from scraper.config import DEFAULT_WARN_STATE_URL  # noqa: E402

log = get_logger(__name__)


def main() -> None:
    # NOTE: warn_state_url must fall back to DEFAULT_WARN_STATE_URL, not
    # None -- get_live_tracker_data() treats a falsy warn_state_url as "skip
    # the WARN Act fallback entirely", which would silently disable the one
    # source that needs zero API credentials.
    raw_df = tracker_scraper.get_live_tracker_data(
        airtable_base_id=os.environ.get("LAYOFFSFYI_AIRTABLE_BASE"),
        warn_state_url=os.environ.get("WARN_STATE_URL", DEFAULT_WARN_STATE_URL),
    )

    raw_dir = REPO_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "tracker_raw_live.csv"
    raw_df.to_csv(raw_path, index=False)
    log.info("Saved %d raw rows to %s", len(raw_df), raw_path)

    cleaned_df = clean.clean_tracker_dataframe(raw_df)

    cleaned_dir = REPO_ROOT / "data" / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = cleaned_dir / "tracker_cleaned.csv"
    cleaned_df.to_csv(cleaned_path, index=False)
    log.info("Saved %d cleaned rows to %s", len(cleaned_df), cleaned_path)

    # Extends data/cleaned/reason_tags_cache.csv in place -- the cache CSV,
    # not tracker_cleaned.csv, is the durable artifact for tags (see
    # pipeline/reasons.py); callers re-merge it at read time via
    # tag_reasons_for_rows(df, max_articles=0).
    max_articles = int(os.environ.get("REASON_TAG_BATCH_SIZE", "50"))
    tagged_df = reasons.tag_reasons_for_rows(cleaned_df, max_articles=max_articles)
    coverage = reasons.summarize_reasons(tagged_df)
    log.info(
        "Reason-tag coverage after this run: %d/%d rows (%.1f%%)",
        coverage["tagged_rows"], coverage["total_rows"], coverage["coverage_pct"],
    )

    source = str(cleaned_df["_source"].iloc[0]) if "_source" in cleaned_df.columns and len(cleaned_df) else "unknown"
    status = {
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(cleaned_df),
        "source": source,
    }
    status_path = cleaned_dir / "last_refresh.json"
    status_path.write_text(json.dumps(status, indent=2))
    log.info("Wrote refresh status to %s: %s", status_path, status)


if __name__ == "__main__":
    main()
