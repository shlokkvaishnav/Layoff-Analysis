"""
forecast_service.py
--------------------
Thin wrapper around pipeline.forecast -- no forecasting logic lives here,
only DataFrame -> JSON-safe dict conversion. Reproduces the ARIMA
ValueError -> naive-only fallback pipeline.forecast.arima_forecast()
documents for short series.
"""

import pandas as pd

from pipeline import forecast as forecast_module  # noqa: E402
from pipeline.eda import STAGE_ORDER  # noqa: E402

from .json_safe import df_records_safe


def _points(fc_df: pd.DataFrame) -> list[dict]:
    out = fc_df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return df_records_safe(out[["date", "forecast", "lower", "upper"]])


def build_forecast(df: pd.DataFrame, group_col: str = None, group_value: str = None, horizon: int = 3) -> dict:
    label = "Overall" if group_col is None else str(group_value)

    series = forecast_module.prepare_monthly_series(df, group_col=group_col, group_value=group_value)
    naive_fc = forecast_module.naive_baseline_forecast(series, horizon=horizon)

    arima_unavailable_reason = None
    arima_model = None
    arima_points: list[dict] = []
    try:
        arima_fc = forecast_module.arima_forecast(series, horizon=horizon)
        arima_model = arima_fc["model"].iloc[0]
        arima_points = _points(arima_fc)
    except ValueError as e:
        arima_unavailable_reason = str(e)

    audit = forecast_module.confidence_audit(series, label)

    historical = [
        {"date": d.strftime("%Y-%m-%d"), "value": None if pd.isna(v) else float(v)}
        for d, v in series.items()
    ]

    return {
        "label": label,
        "months_of_history": len(series),
        "historical": historical,
        "naive": {"model": naive_fc["model"].iloc[0], "points": _points(naive_fc), "unavailable_reason": None},
        "arima": {"model": arima_model, "points": arima_points, "unavailable_reason": arima_unavailable_reason},
        "confidence_audit": {"assumptions": audit["assumptions"]},
    }


def forecast_options(df: pd.DataFrame) -> dict:
    stages = []
    if "stage" in df.columns:
        present = set(df["stage"].dropna().unique())
        stages = [s for s in STAGE_ORDER if s in present]
    sectors = sorted(df["sector"].dropna().unique().tolist())
    return {"overall": True, "stage": stages, "sector": sectors}
