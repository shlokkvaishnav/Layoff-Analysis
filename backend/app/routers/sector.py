from fastapi import APIRouter, Depends

from .. import state
from ..models.sector import ImputationResponse, SectorBreakdown, TreemapResponse
from ..services import aggregations
from ..services.filters import FilterParams

router = APIRouter()


@router.get("/breakdown", response_model=SectorBreakdown)
def breakdown(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.by_sector(df)


@router.get("/treemap", response_model=TreemapResponse)
def treemap_endpoint(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.treemap(df)


@router.get("/imputation", response_model=ImputationResponse)
def imputation(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return aggregations.imputation_breakdown(df)
