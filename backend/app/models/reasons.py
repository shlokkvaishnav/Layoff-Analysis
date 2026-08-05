from typing import List
from pydantic import BaseModel


class ReasonSummary(BaseModel):
    coverage_pct: float
    tagged_rows: int
    total_rows: int


class ReasonCount(BaseModel):
    reason: str
    count: int


class ReasonFrequencyResponse(BaseModel):
    coverage_pct: float
    counts: List[ReasonCount]


class ReasonByStage(BaseModel):
    stage: str
    reason: str
    count: int


class ReasonByQuarter(BaseModel):
    quarter: str
    reason: str
    count: int
