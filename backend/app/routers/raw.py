import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from .. import state
from ..models.raw import PaginatedRaw
from ..services.filters import FilterParams
from ..services.json_safe import df_records_safe

router = APIRouter()

SORTABLE_COLUMNS = {"date", "company", "sector", "laid_off", "stage", "country"}


@router.get("", response_model=PaginatedRaw)
def list_raw(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    filters: FilterParams = Depends(),
):
    df = filters.apply(state.get_data())
    if sort_by in df.columns and sort_by in SORTABLE_COLUMNS:
        df = df.sort_values(sort_by, ascending=(sort_dir == "asc"))
    total = len(df)
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size].copy()
    if "date" in page_df.columns:
        page_df["date"] = page_df["date"].dt.strftime("%Y-%m-%d")
    return {"rows": df_records_safe(page_df), "total": total, "page": page, "page_size": page_size}


@router.get("/export.csv")
def export_csv(filters: FilterParams = Depends()):
    df = filters.apply(state.get_data())
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=layoffs_filtered.csv"},
    )
