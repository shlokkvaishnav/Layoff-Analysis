from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .. import state
from ..models.forecast import ForecastOptions, ForecastResponse
from ..services import forecast_service

router = APIRouter()


@router.get("/options", response_model=ForecastOptions)
def options():
    return forecast_service.forecast_options(state.get_data())


@router.get("", response_model=ForecastResponse)
def forecast(
    group_col: Optional[str] = Query(None, pattern="^(stage|sector)$"),
    group_value: Optional[str] = Query(None),
    horizon: int = Query(3, ge=1, le=12),
):
    if group_col is not None and not group_value:
        raise HTTPException(400, "group_value is required when group_col is set")
    # Forecast always runs on the FULL series, not the active sector/stage/
    # country/date filter set -- a forecast on an already-sliced series
    # would be noisier and less defensible than the whole history.
    df = state.get_data()
    try:
        return forecast_service.build_forecast(df, group_col=group_col, group_value=group_value, horizon=horizon)
    except ValueError as e:
        raise HTTPException(400, str(e))
