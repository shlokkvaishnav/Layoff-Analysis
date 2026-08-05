"""
aggregations.py
----------------
Pure-pandas aggregations mirroring pipeline/eda.py's plot_* groupby logic,
re-expressed as JSON-safe records instead of go.Figure objects (which aren't
portable to the React frontend). pipeline/eda.py itself is left untouched --
each function below names the eda.py function it mirrors so the two stay in
sync if the groupby logic ever changes there.
"""

import pandas as pd

from pipeline.eda import STAGE_ORDER  # noqa: E402

from .json_safe import df_records_safe


def monthly_trend(df: pd.DataFrame, value_col: str = "laid_off") -> list[dict]:
    """Mirrors eda.py::plot_monthly_trend."""
    agg = df.groupby("month", as_index=False)[value_col].sum().sort_values("month")
    agg = agg.rename(columns={value_col: "laid_off"})
    return df_records_safe(agg)


def moving_average(df: pd.DataFrame, value_col: str = "laid_off", window_days: int = 30) -> list[dict]:
    """Mirrors eda.py::plot_moving_average."""
    daily = df.groupby("date", as_index=False)[value_col].sum().sort_values("date")
    daily["moving_avg"] = daily[value_col].rolling(window=window_days, min_periods=1).mean()
    daily = daily.rename(columns={value_col: "laid_off"})
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    return df_records_safe(daily)


def by_stage(df: pd.DataFrame, value_col: str = "laid_off") -> list[dict]:
    """
    Mirrors eda.py::plot_by_stage. Pre-ordered by STAGE_ORDER (fixed color
    assignment on the frontend depends on a stable order, not a value sort).
    """
    if "stage" not in df.columns:
        return []
    agg = df.groupby("stage").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reindex(STAGE_ORDER).dropna(how="all").reset_index()
    return df_records_safe(agg)


def by_country(df: pd.DataFrame, value_col: str = "laid_off", top_n: int = 10) -> list[dict]:
    """Mirrors eda.py::plot_by_country."""
    if "country" not in df.columns:
        return []
    agg = df.groupby("country")[value_col].sum().sort_values(ascending=False).head(top_n).reset_index()
    agg = agg.rename(columns={value_col: "laid_off"})
    return df_records_safe(agg)


def by_sector(df: pd.DataFrame, value_col: str = "laid_off") -> dict:
    """Mirrors eda.py::plot_by_sector; other_unknown_pct powers the frontend's Other/Unknown caveat caption."""
    agg = df.groupby("sector").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reset_index().sort_values("total_laid_off", ascending=False)

    total = df[value_col].sum()
    other_unknown = df.loc[df["sector"].isin(["Other", "Unknown"]), value_col].sum()
    other_unknown_pct = round(100 * other_unknown / total, 1) if total else 0.0

    return {"buckets": df_records_safe(agg), "other_unknown_pct": other_unknown_pct}


def treemap(df: pd.DataFrame, value_col: str = "laid_off") -> dict:
    """Mirrors eda.py::plot_treemap."""
    plot_df = df.dropna(subset=["sector", "company"]).copy()
    plot_df = plot_df[plot_df[value_col] > 0]
    plot_df["sector"] = plot_df["sector"].fillna("Unknown")

    sectors_out = []
    for sector_name, sector_df in plot_df.groupby("sector"):
        companies = (
            sector_df.groupby("company")[value_col].sum()
            .sort_values(ascending=False).reset_index()
            .rename(columns={value_col: "laid_off"})
        )
        sectors_out.append({
            "sector": sector_name,
            "total": float(sector_df[value_col].sum()),
            "companies": df_records_safe(companies),
        })
    sectors_out.sort(key=lambda s: s["total"], reverse=True)
    return {"sectors": sectors_out}


def imputation_breakdown(df: pd.DataFrame, value_col: str = "laid_off") -> dict:
    """Mirrors eda.py::plot_imputation_breakdown / plot_imputed_vs_reported."""
    d = df.copy()
    d["source_type"] = d["_headcount_imputed"].map({True: "imputed", False: "reported"})
    overall = d.groupby("source_type")[value_col].sum().to_dict()
    monthly = d.groupby(["month", "source_type"], as_index=False)[value_col].sum()
    monthly = monthly.rename(columns={value_col: "laid_off"})
    return {
        "overall": {"reported": float(overall.get("reported", 0)), "imputed": float(overall.get("imputed", 0))},
        "monthly": df_records_safe(monthly),
    }
