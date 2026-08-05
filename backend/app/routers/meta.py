import json

from fastapi import APIRouter, Depends

from .. import state
from ..config import settings
from ..models.meta import FilterOptions, FreshnessResponse, HealthResponse, SummaryResponse
from ..services.filters import FilterParams
from pipeline.eda import STAGE_ORDER  # noqa: E402

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@router.get("/summary", response_model=SummaryResponse)
def summary(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    return {
        "total_rows": len(df),
        "people_affected_sum": float(df["laid_off"].sum()),
        "distinct_companies": int(df["company"].nunique()),
        "imputed_rows": int(df["_headcount_imputed"].sum()),
    }


@router.get("/freshness", response_model=FreshnessResponse)
def freshness():
    path = settings.DATA_DIR / "cleaned" / "last_refresh.json"
    if not path.exists():
        return {"last_refreshed_at": None, "source": None, "row_count": None}
    data = json.loads(path.read_text())
    return {
        "last_refreshed_at": data.get("refreshed_at"),
        "source": data.get("source"),
        "row_count": data.get("row_count"),
    }


@router.get("/filters", response_model=FilterOptions)
def filters_options():
    df = state.get_data()
    present_stages = set(df["stage"].dropna().unique()) if "stage" in df.columns else set()
    stages = [s for s in STAGE_ORDER if s in present_stages]
    countries = sorted(df["country"].dropna().unique().tolist()) if "country" in df.columns else []
    has_dates = df["date"].notna().any()
    return {
        "sectors": sorted(df["sector"].dropna().unique().tolist()),
        "stages": stages,
        "countries": countries,
        "date_min": df["date"].min().strftime("%Y-%m-%d") if has_dates else None,
        "date_max": df["date"].max().strftime("%Y-%m-%d") if has_dates else None,
    }
