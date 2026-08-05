"""
main.py
-------
FastAPI entry point. Loads the tracker dataset once at startup (state.py)
and serves fast, read-only JSON over it. No endpoint here ever triggers a
live scrape or live article fetch -- those only run in the scheduled
refresh job (scripts/refresh_data.py). Run with:
    cd backend && uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import state
from .config import settings
from .routers import forecast, meta, raw, reasons, sector, trend


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.load_data()
    yield


app = FastAPI(title="Layoff Pulse 2026 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(meta.router, prefix="/api/meta", tags=["meta"])
app.include_router(trend.router, prefix="/api/trend", tags=["trend"])
app.include_router(sector.router, prefix="/api/sector", tags=["sector"])
app.include_router(reasons.router, prefix="/api/reasons", tags=["reasons"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["forecast"])
app.include_router(raw.router, prefix="/api/raw", tags=["raw"])
