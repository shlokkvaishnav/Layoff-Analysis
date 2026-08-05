from typing import List

from fastapi import APIRouter, Depends

from .. import state
from ..models.reasons import ReasonByQuarter, ReasonByStage, ReasonFrequencyResponse, ReasonSummary
from ..services import reasons_service
from ..services.filters import FilterParams

router = APIRouter()


@router.get("/summary", response_model=ReasonSummary)
def summary(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return reasons_service.summary(df)


@router.get("/frequency", response_model=ReasonFrequencyResponse)
def frequency(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return reasons_service.frequency(df)


@router.get("/by-stage", response_model=List[ReasonByStage])
def by_stage(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return reasons_service.by_stage(df)


@router.get("/over-time", response_model=List[ReasonByQuarter])
def over_time(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return reasons_service.over_time(df)
