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


def prepare_monthly_series(df: pd.DataFrame, sector: str, value_col: str = "laid_off") -> pd.Series:
    """Build a monthly time series for a single sector, filling gap months with 0."""
    sub = df[df["sector"] == sector].copy()
    if sub.empty:
        raise ValueError(f"No rows found for sector '{sector}'.")
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


def plot_forecast_comparison(series: pd.Series, naive_fc: pd.DataFrame, arima_fc: pd.DataFrame, sector: str) -> go.Figure:
    """
    Plot historical series + both forecasts with visible uncertainty bands.
    Bands are drawn as filled areas, not just error bars, so the widening
    (or non-widening) uncertainty is immediately visually obvious.
    """
    fig = go.Figure()

    fig.add_scatter(x=series.index, y=series.values, name="Historical", mode="lines+markers",
                     line=dict(color="black"))

    for fc, color in [(naive_fc, "orange"), (arima_fc, "royalblue")]:
        model_name = fc["model"].iloc[0]
        fig.add_scatter(x=fc["date"], y=fc["forecast"], name=f"{model_name} forecast",
                         mode="lines+markers", line=dict(color=color, dash="dash"))
        fig.add_scatter(
            x=pd.concat([fc["date"], fc["date"][::-1]]),
            y=pd.concat([fc["upper"], fc["lower"][::-1]]),
            fill="toself", fillcolor=color, opacity=0.15,
            line=dict(width=0), showlegend=True, name=f"{model_name} 95% band",
        )

    fig.update_layout(
        title=f"Layoff Forecast Comparison — {sector} (Naive Baseline vs ARIMA)",
        xaxis_title="Month", yaxis_title="People Laid Off",
        hovermode="x unified",
    )
    return fig


def confidence_audit(series: pd.Series, sector: str) -> dict:
    """
    Produce a structured list of assumptions the forecast rests on, and a
    rough flag for how shaky each one is given the actual data at hand.
    This is a DELIVERABLE, not a decoration -- print/display it before any
    forecast number is treated as a claim.
    """
    n_months = len(series)
    audit = {
        "sector": sector,
        "months_of_history": n_months,
        "assumptions": [
            {
                "assumption": "Recent trend continues (no regime change)",
                "shaky_if": "A single mega-announcement or policy shift (rate cut, new AI capex cycle) breaks the pattern",
                "risk_level": "HIGH",
            },
            {
                "assumption": "Tracker coverage of this sector is stable over time",
                "shaky_if": "The tracker started covering this sector more/less completely partway through the window",
                "risk_level": "MEDIUM",
            },
            {
                "assumption": "Series has enough history for the model to fit meaningfully",
                "shaky_if": n_months < 12,
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
    df = pd.read_csv("../data/cleaned/tracker_cleaned.csv")
    top_sector = df.groupby("sector")["laid_off"].sum().idxmax()
    series = prepare_monthly_series(df, top_sector)

    naive_fc = naive_baseline_forecast(series, horizon=3)
    try:
        arima_fc = arima_forecast(series, horizon=3)
    except ValueError as e:
        print(f"ARIMA skipped: {e}")
        arima_fc = naive_fc.copy()
        arima_fc["model"] = "ARIMA_unavailable_fallback_to_naive"

    fig = plot_forecast_comparison(series, naive_fc, arima_fc, top_sector)
    fig.show()

    audit = confidence_audit(series, top_sector)
    print("\nConfidence Audit:")
    for a in audit["assumptions"]:
        print(f"  - [{a['risk_level']}] {a['assumption']} (shaky if: {a['shaky_if']})")
