"""
filters.py
----------
Shared query-param filtering, applied by every router before aggregation:
sector/date-range plus stage/country now that those dimensions exist
(pipeline/clean.py).
"""

from datetime import date
from typing import Optional

import pandas as pd
from fastapi import Query


class FilterParams:
    def __init__(
        self,
        sector: Optional[str] = Query(None),
        stage: Optional[str] = Query(None),
        country: Optional[str] = Query(None),
        date_from: Optional[date] = Query(None),
        date_to: Optional[date] = Query(None),
    ):
        self.sector = sector
        self.stage = stage
        self.country = country
        self.date_from = date_from
        self.date_to = date_to

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df
        if self.sector:
            out = out[out["sector"] == self.sector]
        if self.stage and "stage" in out.columns:
            out = out[out["stage"] == self.stage]
        if self.country and "country" in out.columns:
            out = out[out["country"] == self.country]
        if self.date_from is not None:
            out = out[out["date"] >= pd.Timestamp(self.date_from)]
        if self.date_to is not None:
            out = out[out["date"] <= pd.Timestamp(self.date_to)]
        return out
