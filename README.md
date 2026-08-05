<div align="center">

# Layoff Pulse

**Trend, reason, and forecast analysis of tech-sector layoffs — built on live, continuously refreshed data.**

[![Live Site](https://img.shields.io/badge/live-layoff--analysis.vercel.app-8B5A2B)](https://layoff-analysis.vercel.app)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)

</div>

<!-- ![Trend dashboard](docs/screenshots/trend.png) -->

## What it is

A full-stack analytics site answering three questions about tech-sector layoffs from real, live-scraped data — not a static Kaggle CSV:

- **Trend** — monthly volume, 30-day moving average, breakdowns by funding stage and country.
- **Reason** — stated causes extracted directly from each layoff's own linked news article.
- **Forecast** — naive baseline vs. ARIMA, with a transparent audit of which assumptions are shaky.

Industry/sector alone turned out to be a weak lens for this data — the largest single "sector" by headcount is an uninformative "Other" catch-all. Funding **Stage** and **Country** are used as the primary lenses instead.

## Live Demo

**[layoff-analysis.vercel.app](https://layoff-analysis.vercel.app)**

## Screenshots

<!--
| Trend | Sector | Forecast |
|---|---|---|
| ![Trend](docs/screenshots/trend.png) | ![Sector](docs/screenshots/sector.png) | ![Forecast](docs/screenshots/forecast.png) |
-->

## Features

- Live scrape → clean → serve pipeline, refreshed daily — no static dataset, no manual updates.
- Fuzzy company-name deduplication, headcount imputation, and structured Stage/Country/AI-flag standardization.
- Reason extraction from each layoff's own source article, with a visible coverage percentage.
- Naive + ARIMA forecasting with a confidence audit that names its own shaky assumptions.
- A dedicated **Insights** page — data-derived observations computed live, not illustrative copy.

## Tech Stack

| | |
|---|---|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind CSS, Recharts, React Three Fiber |
| **Backend** | FastAPI, Pandas, statsmodels (ARIMA) |
| **Data collection** | BeautifulSoup, Playwright, feedparser |
| **Infra** | GitHub Actions, Vercel, Render |

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** — system design, data pipeline, backend/frontend structure, deployment.
- **[Local Setup](docs/SETUP.md)** — running the backend, frontend, and data refresh locally.
