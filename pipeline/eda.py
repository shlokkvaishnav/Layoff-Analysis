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
    agg = df.groupby("sector").agg(
        total_laid_off=(value_col, "sum"),
        company_count=("company", "nunique"),
    ).reset_index().sort_values("total_laid_off", ascending=False)

    fig = go.Figure()
    fig.add_bar(x=agg["sector"], y=agg["total_laid_off"], name="Total Laid Off", yaxis="y1", marker_color=BROWN_CREME)
    fig.add_scatter(
        x=agg["sector"], y=agg["company_count"], name="Distinct Companies",
        yaxis="y2", mode="markers+lines", marker=dict(size=10, color=CREME),
    )
    fig.update_layout(
        title="Layoffs by Sector vs. Number of Companies Tracked",
        yaxis=dict(title="Total People Laid Off"),
        yaxis2=dict(title="Companies Tracked", overlaying="y", side="right"),
        legend=dict(x=0.8, y=0.9),
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
