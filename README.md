<div align="center">

# Layoff Pulse 2026

**Trend, reason, and forecast analysis of tech-sector layoffs — built on live, continuously refreshed data.**

[![Live Site](https://img.shields.io/badge/live-layoff--analysis.vercel.app-8B5A2B)](https://layoff-analysis.vercel.app)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)
![Recharts](https://img.shields.io/badge/charts-Recharts-8884d8)

</div>

<!-- ![Trend dashboard](docs/screenshots/trend.png) -->

## What it is

A full-stack analytics site answering three questions about tech-sector layoffs from real, live-scraped data — not a static Kaggle CSV:

- **Trend** — monthly volume, 30-day moving average, breakdowns by funding stage and country.
- **Reason** — stated causes extracted directly from each layoff's own linked news article.
- **Forecast** — naive baseline vs. ARIMA, with a transparent audit of which assumptions are shaky.

Industry/sector alone turned out to be a weak lens for this data — the largest single "sector" by headcount is an uninformative "Other" catch-all. Funding **Stage** and **Country** are better-populated, more reliable dimensions, used throughout instead.

## Screenshots

<!--
| Trend | Sector | Forecast |
|---|---|---|
| ![Trend](docs/screenshots/trend.png) | ![Sector](docs/screenshots/sector.png) | ![Forecast](docs/screenshots/forecast.png) |
-->

## Live Demo

- **Site:** [layoff-analysis.vercel.app](https://layoff-analysis.vercel.app)
- **API:** [layoff-pulse-backend.onrender.com/api/meta/health](https://layoff-pulse-backend.onrender.com/api/meta/health)

> The backend runs on Render's free tier and sleeps after ~15 min idle — first load after a quiet period may take 30–60s to wake up.

## Features

- Live scrape → clean → serve pipeline, refreshed daily via a scheduled job — no static dataset, no manual updates.
- Fuzzy company-name deduplication, headcount imputation, and structured Stage/Country/AI-flag standardization.
- Reason extraction from each layoff's own source article, with a visible coverage percentage rather than a black-box claim.
- Naive + ARIMA forecasting with a confidence audit that names its own shaky assumptions.
- Zero API tokens required to run — the primary data source is a token-free live scrape.

## Tech Stack

| | |
|---|---|
| **Frontend** | Next.js 16 (App Router), TypeScript, Tailwind CSS, Recharts, React Three Fiber |
| **Backend** | FastAPI, Pandas, statsmodels (ARIMA) |
| **Data collection** | BeautifulSoup, Playwright, feedparser |
| **Infra** | GitHub Actions (scheduled refresh), Vercel, Render |

## Architecture

```
scraper/    → live data collection (layoffs.fyi, news RSS + articles)
pipeline/   → cleaning, standardization, reason-tagging, forecasting
backend/    → FastAPI read-only JSON API over the cleaned dataset
frontend/   → Next.js site consuming that API
scripts/    → scheduled refresh entry point (scrape → clean → tag → commit)
```

The API never scrapes live — a scheduled GitHub Actions job
(`.github/workflows/refresh-data.yml`) does that once daily and commits the
result; the backend just serves it. This keeps every page load fast and
keeps the free-tier backend from ever timing out on a live scrape.

<details>
<summary>Full directory structure</summary>

```
LayoffAnalysis/
├── scraper/              tracker_scraper.py, news_scraper.py, config.py
├── pipeline/              clean.py, reasons.py, eda.py, forecast.py, config.py
├── backend/                FastAPI app/{main,state,config}.py, models/, routers/, services/
├── frontend/                Next.js app/, components/, lib/
├── scripts/refresh_data.py
├── .github/workflows/refresh-data.yml
├── render.yaml
└── data/{raw,cleaned}/
```
</details>

## Running Locally

```bash
# Backend
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev

# Manually refresh the data (optional — same as the scheduled job)
pip install -r requirements.txt && playwright install chromium
python scripts/refresh_data.py
```

## Deploying

| Service | Where | Config |
|---|---|---|
| Frontend | Vercel (free) | Root Directory: `frontend`, env: `NEXT_PUBLIC_API_BASE_URL` |
| Backend | Render (free) | `render.yaml` Blueprint, env: `FRONTEND_ORIGINS` |
| Data refresh | GitHub Actions (free) | `.github/workflows/refresh-data.yml`, no secrets required |

## Notes on the Data

- **No API tokens required.** The primary source (`scrape_layoffsfyi_airtable`) captures a signed URL via a one-time headless-browser visit, then a single plain, unauthenticated `GET`.
- **Reason-tagging is deliberately keyword-based**, not real NLP — its coverage percentage is always shown alongside it rather than hidden.
- **ARIMA's order is fixed, not auto-tuned**, so its assumptions stay visible; a confidence audit flags when a series has too little history to trust.
- **If every live source fails**, the scheduled refresh exits non-zero and nothing gets committed — the site keeps serving last known-good data instead of going stale silently.
