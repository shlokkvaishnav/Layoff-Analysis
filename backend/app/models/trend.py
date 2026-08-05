from typing import Optional
from pydantic import BaseModel


class MonthlyPoint(BaseModel):
    month: str
    laid_off: Optional[float] = None


class MovingAveragePoint(BaseModel):
    date: str
    laid_off: Optional[float] = None
    moving_avg: Optional[float] = None


class StageBucket(BaseModel):
    stage: str
    total_laid_off: Optional[float] = None
    company_count: Optional[int] = None


class CountryBucket(BaseModel):
    country: str
    laid_off: Optional[float] = None
