from typing import List

from fastapi import APIRouter, Depends, Query

from .. import state
from ..models.trend import CountryBucket, MonthlyPoint, MovingAveragePoint, StageBucket
from ..services import aggregations
from ..services.filters import FilterParams

router = APIRouter()


@router.get("/monthly", response_model=List[MonthlyPoint])
def monthly(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.monthly_trend(df)


@router.get("/moving-average", response_model=List[MovingAveragePoint])
def moving_average(window_days: int = Query(30, ge=1, le=180), filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.moving_average(df, window_days=window_days)


@router.get("/by-stage", response_model=List[StageBucket])
def by_stage(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.by_stage(df)


@router.get("/by-country", response_model=List[CountryBucket])
def by_country(top_n: int = Query(10, ge=1, le=50), filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.by_country(df, top_n=top_n)
