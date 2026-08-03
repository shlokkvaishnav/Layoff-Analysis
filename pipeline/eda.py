"""
eda.py
------
Reusable EDA plotting functions using Plotly, so the live presentation gets
hover/zoom interactivity instead of static images. Each function returns a
Plotly figure object -- call .show() on it in the notebook.

Every chart function is paired (in the notebook) with an embedded markdown
checkpoint question -- these functions just produce the visual; the
questions live in the notebook cells, deliberately left unanswered.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def plot_monthly_trend(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    """Total layoffs by month -- the base trend line checkpoint question sits after this."""
    monthly = df.groupby("month", as_index=False)[value_col].sum().sort_values("month")
    fig = px.line(
        monthly, x="month", y=value_col, markers=True,
        title="Reported Layoffs by Month (Live-Scraped Data)",
        labels={"month": "Month", value_col: "People Laid Off"},
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_by_sector(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    """
    Layoffs by sector, alongside COMPANY COUNT per sector -- deliberately
    plotted together so the "is this a real spike or a base-rate artifact
    of more companies being tracked in that sector?" question has the data
    it needs sitting right next to it, not hidden in a separate cell.
    """
    agg = df.groupby("sector").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reset_index().sort_values("total_laid_off", ascending=False)

    fig = go.Figure()
    fig.add_bar(x=agg["sector"], y=agg["total_laid_off"], name="Total Laid Off", yaxis="y1")
    fig.add_scatter(
        x=agg["sector"], y=agg["company_count"], name="Distinct Companies Tracked",
        yaxis="y2", mode="markers+lines", marker=dict(size=10),
    )
    fig.update_layout(
        title="Layoffs by Sector vs. Number of Companies Tracked in That Sector",
        yaxis=dict(title="Total People Laid Off"),
        yaxis2=dict(title="Distinct Companies Tracked", overlaying="y", side="right"),
        xaxis=dict(title="Sector", tickangle=-30),
        legend=dict(orientation="h", y=1.15),
    )
    return fig


def plot_by_company_size(df: pd.DataFrame, size_col: str = "company_size", value_col: str = "laid_off") -> go.Figure:
    """Layoffs bucketed by company size band, where size data is available."""
    if size_col not in df.columns or df[size_col].isna().all():
        raise ValueError(
            f"Column '{size_col}' not present or entirely missing -- this source "
            "may not report company size. Worth noting live as a data-availability gap."
        )
    bins = [0, 50, 200, 1000, 5000, float("inf")]
    labels = ["<50", "50-200", "200-1000", "1000-5000", "5000+"]
    df = df.copy()
    df["size_band"] = pd.cut(df[size_col], bins=bins, labels=labels)
    agg = df.groupby("size_band", as_index=False, observed=True)[value_col].sum()
    fig = px.bar(
        agg, x="size_band", y=value_col,
        title="Layoffs by Company Size Band",
        labels={"size_band": "Company Size (employees)", value_col: "People Laid Off"},
    )
    return fig


def plot_by_geography(df: pd.DataFrame, geo_col: str = "location", value_col: str = "laid_off", top_n: int = 15) -> go.Figure:
    """Top-N geographies by total layoffs -- horizontal bar for label readability."""
    if geo_col not in df.columns:
        raise ValueError(f"Column '{geo_col}' not present in this dataset.")
    agg = (
        df.groupby(geo_col, as_index=False)[value_col].sum()
        .sort_values(value_col, ascending=False)
        .head(top_n)
    )
    fig = px.bar(
        agg.sort_values(value_col), x=value_col, y=geo_col, orientation="h",
        title=f"Top {top_n} Geographies by Reported Layoffs",
        labels={value_col: "People Laid Off", geo_col: "Location"},
    )
    return fig


def plot_imputed_vs_reported(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    """
    Stacked monthly bar splitting reported vs. imputed headcount numbers.
    Directly supports the "what would a lazy analysis conclude, and why
    would it be wrong?" checkpoint -- a lazy read of the monthly trend
    ignores how much of it is imputed rather than reported.
    """
    df = df.copy()
    df["source_type"] = df["_headcount_imputed"].map({True: "Imputed", False: "Reported"})
    agg = df.groupby(["month", "source_type"], as_index=False)[value_col].sum()
    fig = px.bar(
        agg, x="month", y=value_col, color="source_type", barmode="stack",
        title="Monthly Layoffs: Reported vs. Imputed Headcount",
        labels={"month": "Month", value_col: "People Laid Off", "source_type": "Data Type"},
    )
    return fig


if __name__ == "__main__":
    df = pd.read_csv("../data/cleaned/tracker_cleaned.csv")
    plot_monthly_trend(df).show()
    plot_by_sector(df).show()
    plot_imputed_vs_reported(df).show()
