"""
forecast.py
-----------
Short-horizon forecasting of layoff activity by sector.

Deliberately shows a NAIVE rolling-average baseline side-by-side with an
ARIMA model -- never present ARIMA alone as if it's obviously superior.
Comparing "dumb baseline vs statistical model" is itself the pedagogical
point: a forecast is only impressive relative to a baseline you've actually
shown, and the gap between them (or lack of one) is honest information.

Every forecast returned includes visible uncertainty bands -- a single
confident line is treated as a bug, not a feature.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")  # ARIMA convergence warnings are noisy in a live demo


def prepare_monthly_series(df: pd.DataFrame, group_col: str = None, group_value: str = None,
                            value_col: str = "laid_off") -> pd.Series:
    """
    Build a monthly time series, filling gap months with 0. With no
    group_col/group_value, this is the overall/national series across the
    whole dataset -- the headline forecast, since it isn't thinned out by a
    segmentation. Pass e.g. group_col="stage", group_value="Series B" for a
    per-cohort series instead (sector remains a valid group_col too, just no
    longer the default).
    """
    if group_col is not None:
        sub = df[df[group_col] == group_value].copy()
        label = f"{group_col}='{group_value}'"
    else:
        sub = df.copy()
        label = "overall"
    if sub.empty:
        raise ValueError(f"No rows found for {label}.")
    sub["month"] = pd.to_datetime(sub["month"])
    monthly = sub.groupby("month")[value_col].sum().sort_index()
    full_range = pd.date_range(monthly.index.min(), monthly.index.max(), freq="MS")
    monthly = monthly.reindex(full_range, fill_value=0)
    return monthly


def naive_baseline_forecast(series: pd.Series, horizon: int = 3, window: int = 3) -> pd.DataFrame:
    """
    Simple rolling-average extrapolation: forecast = mean of the last
    `window` months, held flat across the horizon. Uncertainty band is the
    historical rolling std dev -- crude but transparent.
    """
    recent_mean = series.tail(window).mean()
    recent_std = series.tail(window).std(ddof=0)
    recent_std = 0.0 if np.isnan(recent_std) else recent_std

    future_index = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    forecast = pd.DataFrame({
        "date": future_index,
        "forecast": recent_mean,
        "lower": max(recent_mean - 1.96 * recent_std, 0),
        "upper": recent_mean + 1.96 * recent_std,
        "model": "naive_rolling_avg",
    })
    return forecast


def arima_forecast(series: pd.Series, horizon: int = 3, order=(1, 1, 1)) -> pd.DataFrame:
    """
    ARIMA forecast with 95% confidence intervals. `order` is left as a
    simple, explicit default (1,1,1) rather than auto-tuned -- worth
    narrating live that auto_arima exists but a fixed, inspectable order
    keeps the demo's assumptions visible and debuggable in real time.
    """
    if len(series) < 6:
        raise ValueError(
            "Series too short for a meaningful ARIMA fit (<6 months of data). "
            "Fall back to naive_baseline_forecast for this sector."
        )

    model = ARIMA(series.values, order=order)
    fitted = model.fit()
    result = fitted.get_forecast(steps=horizon)
    conf_int = result.conf_int(alpha=0.05)

    future_index = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    forecast = pd.DataFrame({
        "date": future_index,
        "forecast": result.predicted_mean,
        "lower": np.clip(conf_int[:, 0], 0, None),
        "upper": conf_int[:, 1],
        "model": f"ARIMA{order}",
    })
    return forecast


def plot_forecast_comparison(series: pd.Series, naive_fc: pd.DataFrame, arima_fc: pd.DataFrame, label: str) -> go.Figure:
    """
    Plot historical series + both forecasts with visible uncertainty bands.
    `label` names whatever segment `series` represents (e.g. "overall",
    a sector, or a funding stage) for the chart title.
    Uses Black and Brown Creme custom theme styling.
    """
    CREME = "#F5F5DC"
    BROWN_CREME = "#D2B48C"
    
    fig = go.Figure()

    fig.add_scatter(x=series.index, y=series.values, name="Historical", mode="lines+markers",
                     line=dict(color=CREME, width=3))

    for fc, color in [(naive_fc, "gray"), (arima_fc, BROWN_CREME)]:
        model_name = fc["model"].iloc[0]
        fig.add_scatter(x=fc["date"], y=fc["forecast"], name=f"{model_name} forecast",
                         mode="lines+markers", line=dict(color=color, dash="dash", width=3))
        
        # Only add confidence interval for ARIMA or if it exists
        if model_name != "Naive":
            fig.add_scatter(
                x=pd.concat([fc["date"], fc["date"][::-1]]),
                y=pd.concat([fc["upper"], fc["lower"][::-1]]),
                fill="toself", fillcolor=color, opacity=0.3,
                line=dict(color='rgba(255,255,255,0)'), showlegend=True, name=f"{model_name} 95% band",
            )

    fig.update_layout(
        title=f"Layoff Forecast Comparison — {label} (Naive vs ARIMA)",
        xaxis_title="Month", yaxis_title="People Laid Off",
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CREME)
    )
    return fig


def confidence_audit(series: pd.Series, label: str) -> dict:
    """
    Produce a structured list of assumptions the forecast rests on, and a
    rough flag for how shaky each one is given the actual data at hand.
    This is a DELIVERABLE, not a decoration -- print/display it before any
    forecast number is treated as a claim.
    """
    n_months = len(series)
    audit = {
        "label": label,
        "months_of_history": n_months,
        "assumptions": [
            {
                "assumption": "Recent trend continues (no regime change)",
                "shaky_if": "A single mega-announcement or policy shift (rate cut, new AI capex cycle) breaks the pattern",
                "risk_level": "HIGH",
            },
            {
                "assumption": "Tracker coverage of this segment is stable over time",
                "shaky_if": "The tracker started covering this segment more/less completely partway through the window",
                "risk_level": "MEDIUM",
            },
            {
                "assumption": "Series has enough history for the model to fit meaningfully",
                "shaky_if": "Fewer than 12 months of history -- ARIMA's fit gets progressively less reliable below that",
                "risk_level": "HIGH" if n_months < 6 else ("MEDIUM" if n_months < 12 else "LOW"),
            },
            {
                "assumption": "Missing/imputed headcount rows don't systematically bias the trend direction",
                "shaky_if": "Imputation was concentrated in recent months rather than spread evenly",
                "risk_level": "MEDIUM",
            },
        ],
    }
    return audit


if __name__ == "__main__":
    from pathlib import Path
    clean_path = Path(__file__).resolve().parent.parent / "data" / "cleaned" / "tracker_cleaned.csv"
    if not clean_path.exists():
        print(f"Error: {clean_path} not found.")
        exit(1)
    df = pd.read_csv(clean_path)
    series = prepare_monthly_series(df)  # overall/national series -- the new headline

    naive_fc = naive_baseline_forecast(series, horizon=3)
    try:
        arima_fc = arima_forecast(series, horizon=3)
    except ValueError as e:
        print(f"ARIMA skipped: {e}")
        arima_fc = naive_fc.copy()
        arima_fc["model"] = "ARIMA_unavailable_fallback_to_naive"

    fig = plot_forecast_comparison(series, naive_fc, arima_fc, "Overall")
    fig.show()

    audit = confidence_audit(series, "Overall")
    print("\nConfidence Audit:")
    for a in audit["assumptions"]:
        print(f"  - [{a['risk_level']}] {a['assumption']} (shaky if: {a['shaky_if']})")
