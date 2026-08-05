from typing import List, Optional
from pydantic import BaseModel


class HistoricalPoint(BaseModel):
    date: str
    value: Optional[float] = None


class ForecastPoint(BaseModel):
    date: str
    forecast: Optional[float] = None
    lower: Optional[float] = None
    upper: Optional[float] = None


class ForecastSeries(BaseModel):
    model: Optional[str] = None
    points: List[ForecastPoint]
    unavailable_reason: Optional[str] = None


class ConfidenceAssumption(BaseModel):
    assumption: str
    shaky_if: str
    risk_level: str


class ConfidenceAudit(BaseModel):
    assumptions: List[ConfidenceAssumption]


class ForecastResponse(BaseModel):
    label: str
    months_of_history: int
    historical: List[HistoricalPoint]
    naive: ForecastSeries
    arima: ForecastSeries
    confidence_audit: ConfidenceAudit


class ForecastOptions(BaseModel):
    overall: bool
    stage: List[str]
    sector: List[str]
