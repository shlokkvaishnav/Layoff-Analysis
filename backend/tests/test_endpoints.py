"""
test_endpoints.py
------------------
Exercises the FastAPI app against a small in-memory fixture DataFrame (not
the real committed CSV), covering both an Airtable-shaped row (has
stage/country/ai_flag/funds_raised_mm) and a WARN-Act-shaped row (missing
those columns entirely) -- this is exactly the shape that catches the
JSON-safety pitfall (NaN/pd.NA reaching the JSON encoder) the plan called out.
Bypasses app.state.load_data()'s CSV read by setting app.state._df directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from fastapi.testclient import TestClient

from app import state
from app.main import app


def make_fixture_df() -> pd.DataFrame:
    df = pd.DataFrame([
        {
            "company": "Acme AI", "date": pd.Timestamp("2026-01-15"), "sector": "AI",
            "laid_off": 50.0, "month": "2026-01", "_headcount_imputed": False,
            "company_original": "Acme AI Inc.", "stage": "Series B", "ai_flag": True,
            "country": "United States", "location_hq": "SF Bay Area", "funds_raised_mm": 120.0,
            "Source": "https://example.com/acme-layoffs", "reason_tags": ["AI", "restructuring"],
        },
        {
            "company": "Beta Retail", "date": pd.Timestamp("2026-02-01"), "sector": "Other",
            "laid_off": 30.0, "month": "2026-02", "_headcount_imputed": True,
            "company_original": "Beta Retail", "stage": "Unknown", "ai_flag": pd.NA,
            "country": "Canada", "location_hq": "Toronto", "funds_raised_mm": float("nan"),
            "Source": "https://example.com/beta-layoffs", "reason_tags": [],
        },
        {
            # WARN-Act-shaped: no stage/ai_flag/country/location_hq/funds_raised_mm/Source at all
            "company": "Gamma Mfg", "date": pd.Timestamp("2026-03-10"), "sector": "Unknown",
            "laid_off": 20.0, "month": "2026-03", "_headcount_imputed": False,
            "company_original": "Gamma Mfg", "reason_tags": [],
        },
    ])
    if "ai_flag" in df.columns:
        df["ai_flag"] = df["ai_flag"].astype("boolean")
    return df


client: TestClient


def setup_module(module):
    global client
    state._df = make_fixture_df()
    client = TestClient(app)


def test_health():
    resp = client.get("/api/meta/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_summary():
    resp = client.get("/api/meta/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == 3


def test_summary_respects_filters():
    # Regression test: summary() originally ignored FilterParams entirely,
    # so selecting a filter in the UI updated the URL but not the KPI tiles.
    resp = client.get("/api/meta/summary", params={"sector": "AI"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == 1
    assert body["people_affected_sum"] == 50.0


def test_filters_include_ai_sector():
    resp = client.get("/api/meta/filters")
    assert resp.status_code == 200
    assert "AI" in resp.json()["sectors"]


def test_trend_monthly():
    resp = client.get("/api/trend/monthly")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_trend_by_stage_ignores_rows_missing_the_column():
    resp = client.get("/api/trend/by-stage")
    assert resp.status_code == 200
    stages = {row["stage"] for row in resp.json()}
    assert "Series B" in stages
    # Gamma Mfg (no stage at all) must not crash the endpoint or appear as a phantom bucket
    assert "Gamma Mfg" not in stages


def test_sector_breakdown_other_unknown_pct():
    resp = client.get("/api/sector/breakdown")
    assert resp.status_code == 200
    body = resp.json()
    assert body["other_unknown_pct"] > 0


def test_sector_treemap():
    resp = client.get("/api/sector/treemap")
    assert resp.status_code == 200


def test_sector_imputation():
    resp = client.get("/api/sector/imputation")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"]["imputed"] == 30.0
    assert body["overall"]["reported"] == 70.0


def test_reasons_summary():
    resp = client.get("/api/reasons/summary")
    assert resp.status_code == 200
    assert resp.json()["tagged_rows"] == 1


def test_reasons_frequency():
    resp = client.get("/api/reasons/frequency")
    assert resp.status_code == 200


def test_forecast_overall():
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    assert resp.json()["label"] == "Overall"


def test_forecast_requires_group_value_with_group_col():
    resp = client.get("/api/forecast", params={"group_col": "stage"})
    assert resp.status_code == 400


def test_raw_pagination_and_nan_serialization():
    resp = client.get("/api/raw", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["rows"]) == 2
    for row in body["rows"]:
        if row["company"] == "Beta Retail":
            # NaN funds_raised_mm must serialize as JSON null, not NaN
            assert row["funds_raised_mm"] is None
