"""
clean.py
--------
Cleaning stage for live-scraped layoff data. This is where the "messy,
ambiguous data" from the scraper stage gets turned into something EDA-ready
-- but note in the demo that cleaning DECISIONS are made here, not just
mechanical fixes, and each one is a judgment call worth surfacing.
"""

import re
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process

SECTOR_STANDARDIZATION_MAP = {
    "ai": "AI",
    "artificial intelligence": "AI",
    "fintech": "Fintech",
    "financial services": "Fintech",
    "healthcare": "Healthcare",
    "health tech": "Healthcare",
    "e-commerce": "E-Commerce",
    "ecommerce": "E-Commerce",
    "retail": "E-Commerce",
    "consumer": "Consumer",
    "enterprise software": "Enterprise Software",
    "saas": "Enterprise Software",
    "hardware": "Hardware",
    "crypto": "Crypto",
    "cryptocurrency": "Crypto",
    "transportation": "Transportation",
    "logistics": "Transportation",
    "media": "Media",
    "gaming": "Gaming",
    "video games": "Gaming",
    "real estate": "Real Estate",
    "edtech": "EdTech",
    "education": "EdTech",
}


def standardize_sector(raw_sector: str) -> str:
    """Map a raw, freeform sector string to a standardized category."""
    if pd.isna(raw_sector) or not str(raw_sector).strip():
        return "Unknown"
    key = str(raw_sector).strip().lower()
    if key in SECTOR_STANDARDIZATION_MAP:
        return SECTOR_STANDARDIZATION_MAP[key]
    # fuzzy fallback against known keys
    match, score, _ = process.extractOne(
        key, SECTOR_STANDARDIZATION_MAP.keys(), scorer=fuzz.token_sort_ratio
    ) or (None, 0, None)
    if match and score >= 80:
        return SECTOR_STANDARDIZATION_MAP[match]
    return str(raw_sector).strip().title()  # leave as-is, title-cased, if truly unmatched


def standardize_date(raw_date) -> pd.Timestamp:
    """Coerce a variety of date formats/strings into a single pd.Timestamp (NaT on failure)."""
    return pd.to_datetime(raw_date, errors="coerce", utc=False)


def dedupe_company_names(df: pd.DataFrame, name_col: str = "company", threshold: int = 85) -> pd.DataFrame:
    """
    Fuzzy-dedupe company name variants (e.g. 'Meta' vs 'Meta Platforms Inc.')
    by clustering names above a similarity threshold and mapping each to the
    shortest/most common representative name in its cluster.

    Uses `token_set_ratio` rather than `token_sort_ratio` -- token_sort_ratio
    scores a short name against a much longer one (e.g. 'Meta' vs 'Meta
    Platforms Inc.') poorly, since it compares full token sequences of very
    different lengths. token_set_ratio instead compares the SET overlap of
    tokens, so a name that's a subset of another scores near 100.

    This is a real tradeoff worth narrating live: token_set_ratio is more
    aggressive and can over-merge unrelated companies that happen to share a
    common word (e.g. 'Meta' and 'Metabase', or two different companies both
    named after a common word like 'Cloud'). Lower the threshold and inspect
    the merged-pairs table below to see exactly what got clustered -- don't
    trust this step blindly.

    This is intentionally shown as a SEPARATE, visible step (not hidden
    inside a groupby) so participants can inspect exactly which names got
    merged and second-guess the threshold.
    """
    df = df.copy()
    names = df[name_col].dropna().astype(str).str.strip().unique().tolist()
    canonical_map = {}
    assigned = set()

    for name in names:
        if name in assigned:
            continue
        cluster = [name]
        assigned.add(name)
        for other in names:
            if other in assigned:
                continue
            if fuzz.token_set_ratio(name, other) >= threshold:
                cluster.append(other)
                assigned.add(other)
        # representative: shortest name in the cluster (usually the "clean" brand name)
        representative = min(cluster, key=len)
        for n in cluster:
            canonical_map[n] = representative

    df["company_original"] = df[name_col]
    df[name_col] = df[name_col].astype(str).str.strip().map(canonical_map).fillna(df[name_col])
    return df


def impute_missing_headcount(df: pd.DataFrame, headcount_col: str = "laid_off",
                              pct_col: str = "percentage", size_col: str = "company_size") -> pd.DataFrame:
    """
    Handle missing headcount numbers with a transparent, tiered strategy
    (rather than silently dropping rows or filling with 0, both of which
    would bias the EDA):

        1. If percentage + company size known -> compute headcount.
        2. Else -> impute with the median headcount for that row's sector.
        3. Else -> leave as NaN and flag it (do NOT silently zero-fill).

    A '_headcount_imputed' boolean column is added so downstream EDA/
    forecasting can choose to exclude imputed rows for sensitivity checks --
    this flag is itself a checkpoint-question prompt ("how much of our
    trend line is real vs imputed?").
    """
    df = df.copy()
    df["_headcount_imputed"] = False

    if pct_col in df.columns and size_col in df.columns:
        computable = df[headcount_col].isna() & df[pct_col].notna() & df[size_col].notna()
        df.loc[computable, headcount_col] = (
            df.loc[computable, pct_col].astype(float) * df.loc[computable, size_col].astype(float)
        )
        df.loc[computable, "_headcount_imputed"] = True

    if "sector" in df.columns:
        sector_medians = df.groupby("sector")[headcount_col].median()
        still_missing = df[headcount_col].isna()
        df.loc[still_missing, headcount_col] = df.loc[still_missing, "sector"].map(sector_medians)
        df.loc[still_missing, "_headcount_imputed"] = True

    return df


def clean_tracker_dataframe(raw_df: pd.DataFrame,
                             company_col: str = "company",
                             date_col: str = "date",
                             sector_col: str = "sector",
                             headcount_col: str = "laid_off") -> pd.DataFrame:
    """
    Full cleaning pipeline entry point. Renames flexibly (raw scrape column
    names vary by source), then applies dedupe -> date standardization ->
    sector standardization -> headcount imputation, in that order.
    """
    df = raw_df.copy()

    # Best-effort column renaming since raw column names differ across
    # sources (Airtable field names vs Apify actor output vs WARN tables).
    rename_candidates = {
        company_col: "company",
        date_col: "date",
        sector_col: "sector",
        headcount_col: "laid_off",
    }
    df = df.rename(columns={k: v for k, v in rename_candidates.items() if k in df.columns})

    for required in ["company", "date", "sector", "laid_off"]:
        if required not in df.columns:
            df[required] = np.nan

    df["date"] = df["date"].apply(standardize_date)
    df["sector"] = df["sector"].apply(standardize_sector)
    df = dedupe_company_names(df, name_col="company")
    df = impute_missing_headcount(df, headcount_col="laid_off")

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df = df.dropna(subset=["date"])  # rows with unparseable dates can't go in a time series

    return df


if __name__ == "__main__":
    raw = pd.read_csv("../data/raw/tracker_raw_live.csv")
    cleaned = clean_tracker_dataframe(raw)
    print(f"Cleaned {len(cleaned)} rows from {len(raw)} raw rows.")
    print(f"Rows with imputed headcount: {cleaned['_headcount_imputed'].sum()}")
    cleaned.to_csv("../data/cleaned/tracker_cleaned.csv", index=False)
