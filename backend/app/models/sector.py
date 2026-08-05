from typing import List, Optional
from pydantic import BaseModel


class SectorBucket(BaseModel):
    sector: str
    total_laid_off: Optional[float] = None
    company_count: Optional[int] = None


class SectorBreakdown(BaseModel):
    buckets: List[SectorBucket]
    other_unknown_pct: float


class TreemapCompany(BaseModel):
    company: str
    laid_off: Optional[float] = None


class TreemapSector(BaseModel):
    sector: str
    total: float
    companies: List[TreemapCompany]


class TreemapResponse(BaseModel):
    sectors: List[TreemapSector]


class ImputationOverall(BaseModel):
    reported: float
    imputed: float


class ImputationMonthlyPoint(BaseModel):
    month: str
    source_type: str
    laid_off: Optional[float] = None


class ImputationResponse(BaseModel):
    overall: ImputationOverall
    monthly: List[ImputationMonthlyPoint]
