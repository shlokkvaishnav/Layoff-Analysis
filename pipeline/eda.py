"""
eda.py
------
Reusable EDA plotting functions using Plotly, updated with a custom Black/Creme Theme.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Global Theme Settings
PLOTLY_THEME = "plotly_dark"
CREME = "#F5F5DC"
BROWN_CREME = "#D2B48C"
DARK_BROWN = "#8B5A2B"
CHARCOAL = "#151515"

def apply_custom_theme(fig: go.Figure):
    fig.update_layout(
        template=PLOTLY_THEME,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CREME)
    )
    return fig

def plot_monthly_trend(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    monthly = df.groupby("month", as_index=False)[value_col].sum().sort_values("month")
    fig = px.line(
        monthly, x="month", y=value_col, markers=True,
        title="Reported Layoffs by Month",
        labels={"month": "Month", value_col: "People Laid Off"},
        color_discrete_sequence=[BROWN_CREME]
    )
    fig.update_layout(hovermode="x unified")
    return apply_custom_theme(fig)

def plot_by_sector(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    """
    Total layoffs by sector. Company count rides along as a hover detail
    rather than a second y-axis -- two measures on different scales read as
    a single chart only when one is folded into the tooltip, not stacked
    onto a competing axis.
    """
    agg = df.groupby("sector").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reset_index().sort_values("total_laid_off", ascending=False)

    fig = px.bar(
        agg, x="sector", y="total_laid_off", custom_data=["company_count"],
        title="Layoffs by Sector",
        labels={"sector": "Sector", "total_laid_off": "People Laid Off"},
        color_discrete_sequence=[BROWN_CREME],
    )
    fig.update_traces(
        hovertemplate="%{x}<br>People laid off: %{y:,}<br>Companies tracked: %{customdata[0]}<extra></extra>"
    )
    return apply_custom_theme(fig)

def plot_imputed_vs_reported(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    df = df.copy()
    df["source_type"] = df["_headcount_imputed"].map({True: "Imputed", False: "Reported"})
    agg = df.groupby(["month", "source_type"], as_index=False)[value_col].sum()
    fig = px.bar(
        agg, x="month", y=value_col, color="source_type", barmode="stack",
        title="Monthly Layoffs: Reported vs. Imputed",
        color_discrete_map={"Reported": BROWN_CREME, "Imputed": DARK_BROWN}
    )
    return apply_custom_theme(fig)

def plot_treemap(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    plot_df = df.dropna(subset=["sector", "company"]).copy()
    plot_df = plot_df[plot_df[value_col] > 0]
    plot_df["sector"] = plot_df["sector"].fillna("Unknown")
    
    fig = px.treemap(
        plot_df, 
        path=[px.Constant("Layoffs"), "sector", "company"], 
        values=value_col,
        title="Layoffs Breakdown: Sector vs Company",
        color=value_col,
        color_continuous_scale=[CREME, BROWN_CREME, DARK_BROWN]
    )
    fig.update_traces(
        root_color=CHARCOAL,
        textfont=dict(color="black", size=14),
        marker=dict(line=dict(width=2, color=CHARCOAL))
    )
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return apply_custom_theme(fig)

# Canonical funding-stage order (see pipeline/clean.py's STAGE_STANDARDIZATION_MAP)
# -- used so plot_by_stage reads as a progression rather than a value sort.
STAGE_ORDER = ["Seed", "Series A", "Series B", "Series C", "Series D", "Series E+",
               "Private Equity", "Acquired", "Subsidiary", "Public", "Unknown"]

# Fixed per-reason color assignment (see scraper/news_scraper.py's
# STATED_REASON_PHRASES) -- a given reason keeps the same color across any
# filtered view rather than being repainted by whatever order it happens to
# appear in a given slice.
REASON_COLOR_MAP = {
    "restructuring": BROWN_CREME,
    "efficiency": DARK_BROWN,
    "streamlin": "#A67B5B",
    "realign": "#C9A66B",
    "cost discipline": "#8B6F47",
    "AI": CREME,
    "automation": "#D8C3A5",
    "macroeconomic": "#6F4E37",
    "market conditions": "#B08968",
    "right-sizing": "#4A3728",
}


def plot_by_stage(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    """
    Layoffs by funding stage -- a well-populated alternative to sector
    (see clean.py's standardize_stage), not dominated by an uninformative
    catch-all the way "Other" dominates sector. Company count rides along
    as a hover detail rather than a second y-axis (see plot_by_sector).
    """
    agg = df.groupby("stage").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reindex(STAGE_ORDER).dropna(how="all").reset_index()

    fig = px.bar(
        agg, x="stage", y="total_laid_off", custom_data=["company_count"],
        title="Layoffs by Funding Stage",
        labels={"stage": "Funding Stage", "total_laid_off": "People Laid Off"},
        color_discrete_sequence=[BROWN_CREME],
    )
    fig.update_traces(
        hovertemplate="%{x}<br>People laid off: %{y:,}<br>Companies tracked: %{customdata[0]}<extra></extra>"
    )
    return apply_custom_theme(fig)


def plot_by_country(df: pd.DataFrame, value_col: str = "laid_off", top_n: int = 10) -> go.Figure:
    """Top countries by total reported layoffs."""
    agg = (
        df.groupby("country")[value_col].sum()
        .sort_values(ascending=False).head(top_n).reset_index()
    )
    fig = px.bar(
        agg, x="country", y=value_col, title=f"Top {top_n} Countries by People Laid Off",
        labels={"country": "Country", value_col: "People Laid Off"},
        color_discrete_sequence=[BROWN_CREME],
    )
    return apply_custom_theme(fig)


def plot_reasons_frequency(df: pd.DataFrame, coverage_pct: float = None) -> go.Figure:
    """
    Bar of stated-reason tag frequency, exploded from `reason_tags` (see
    pipeline/reasons.py::tag_reasons_for_rows). `coverage_pct` -- the share
    of rows that actually have a tagged article -- is folded into the title
    so this is never read as more complete than it is.
    """
    if "reason_tags" not in df.columns:
        raise ValueError("df has no 'reason_tags' column -- run pipeline.reasons.tag_reasons_for_rows() first.")

    exploded = df.explode("reason_tags").dropna(subset=["reason_tags"])
    counts = exploded["reason_tags"].value_counts().reset_index()
    counts.columns = ["reason", "count"]

    title = "Stated Layoff Reasons (from tagged news articles)"
    if coverage_pct is not None:
        title += f" — based on {coverage_pct:.1f}% of rows with a tagged article"

    fig = px.bar(
        counts, x="reason", y="count", title=title,
        labels={"reason": "Stated Reason", "count": "Mentions"},
        color_discrete_sequence=[DARK_BROWN],
    )
    return apply_custom_theme(fig)


def plot_reasons_over_time(df: pd.DataFrame) -> go.Figure:
    """Stated-reason tag frequency by quarter (see pipeline/reasons.py)."""
    if "reason_tags" not in df.columns:
        raise ValueError("df has no 'reason_tags' column -- run pipeline.reasons.tag_reasons_for_rows() first.")

    exploded = df.explode("reason_tags").dropna(subset=["reason_tags"]).copy()
    exploded["quarter"] = pd.to_datetime(exploded["date"], errors="coerce").dt.to_period("Q").astype(str)
    agg = exploded.groupby(["quarter", "reason_tags"], as_index=False).size()

    fig = px.bar(
        agg, x="quarter", y="size", color="reason_tags", barmode="stack",
        title="Stated Layoff Reasons Over Time",
        labels={"quarter": "Quarter", "size": "Mentions", "reason_tags": "Stated Reason"},
    )
    return apply_custom_theme(fig)


def plot_moving_average(df: pd.DataFrame, value_col: str = "laid_off", window_days: int = 30) -> go.Figure:
    daily = df.groupby("date", as_index=False)[value_col].sum().sort_values("date")
    daily["MA"] = daily[value_col].rolling(window=window_days, min_periods=1).mean()
    
    fig = go.Figure()
    fig.add_scatter(x=daily["date"], y=daily[value_col], mode="markers", opacity=0.4, name="Daily Spikes", marker=dict(color="gray"))
    fig.add_scatter(x=daily["date"], y=daily["MA"], mode="lines", name=f"{window_days}-Day Moving Average", line=dict(color=BROWN_CREME, width=3))
    
    fig.update_layout(
        title=f"Layoffs Timeline ({window_days}-Day Moving Average)",
        xaxis_title="Date",
        yaxis_title="People Laid Off",
        hovermode="x unified"
    )
    return apply_custom_theme(fig)

def plot_imputation_breakdown(df: pd.DataFrame, value_col: str = "laid_off") -> go.Figure:
    df = df.copy()
    df["source_type"] = df["_headcount_imputed"].map({True: "Imputed", False: "Reported"})
    agg = df.groupby("source_type", as_index=False)[value_col].sum()
    
    fig = px.pie(
        agg, names="source_type", values=value_col, hole=0.4,
        title="Data Integrity: Reported vs Imputed",
        color="source_type",
        color_discrete_map={"Reported": BROWN_CREME, "Imputed": DARK_BROWN}
    )
    return apply_custom_theme(fig)

if __name__ == "__main__":
    from pathlib import Path
    clean_path = Path(__file__).resolve().parent.parent / "data" / "cleaned" / "tracker_cleaned.csv"
    if not clean_path.exists():
        print(f"Error: {clean_path} not found.")
        exit(1)
    df = pd.read_csv(clean_path)
    df["date"] = pd.to_datetime(df["date"])
    
    plot_monthly_trend(df).show()
    plot_treemap(df).show()
