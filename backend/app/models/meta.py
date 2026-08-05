from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SummaryResponse(BaseModel):
    total_rows: int
    people_affected_sum: float
    distinct_companies: int
    imputed_rows: int


class FreshnessResponse(BaseModel):
    last_refreshed_at: Optional[str] = None
    source: Optional[str] = None
    row_count: Optional[int] = None


class FilterOptions(BaseModel):
    sectors: List[str]
    stages: List[str]
    countries: List[str]
    date_min: Optional[str] = None
    date_max: Optional[str] = None
