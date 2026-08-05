# Layoff Pulse 2026

A trend / reason / forecast website for tech layoffs, built on a live
scrape → clean → serve pipeline. The deployed product is a Next.js
frontend backed by a FastAPI API; a scheduled job keeps the underlying data
current without any request ever triggering a live scrape.

## Why this exists

Layoffs are continuous, heavily covered news — a live, scrapeable dataset
rather than a static Kaggle CSV. The site is organized around three
questions: what's the **trend**, what **reason** do companies give, and
what does that imply about the **future**. Sector/Industry alone turned out
to be a weak lens for this (the largest single "sector" by headcount is an
uninformative "Other" catch-all) — funding **Stage** and **Country** are
better-populated, more reliable structured dimensions, and stated reasons
are extracted directly from each layoff's own linked news source.

## Architecture

```
LayoffAnalysis/
├── scraper/                 # live: layoffs.fyi (Airtable shared-view → Apify → WARN Act fallback chain),
│   │                          RSS headlines + article text + naive reason-tagging
│   ├── tracker_scraper.py
│   ├── news_scraper.py
│   └── config.py
├── pipeline/                 # cleaning, aggregation, and forecasting logic (framework-agnostic)
│   ├── clean.py              # fuzzy company dedupe, sector/stage/country standardization, headcount imputation
│   ├── reasons.py            # merges news-scraper reason-tags onto tracker rows, cache-backed
│   ├── eda.py                # chart-ready aggregations (mirrored by backend/app/services/aggregations.py)
│   ├── forecast.py           # naive rolling-avg baseline + ARIMA, confidence-interval audit
│   └── config.py
├── backend/                  # FastAPI -- wraps pipeline/scraper as a fast, read-only JSON API
│   └── app/{main,state,config}.py, models/, routers/, services/
├── frontend/                  # Next.js + Recharts -- the deployed site (Trend, Sector, Reasons, Forecast, Raw)
├── scripts/
│   └── refresh_data.py        # scheduled entry point: scrape -> clean -> tag reasons -> write status
├── .github/workflows/
│   └── refresh-data.yml       # daily cron running refresh_data.py, commits data/ back to the repo
├── render.yaml                 # Render Blueprint for the backend
└── data/
    ├── raw/                    # latest raw scrape
    └── cleaned/                # cleaned dataset, reason-tag cache, last_refresh.json
```

**Why the API never scrapes live:** `tracker_scraper.get_live_tracker_data()`
can take up to ~300s (Apify fallback), and reason-tagging does live
per-article HTTP fetches. Neither happens inside a request — `backend/`
loads `data/cleaned/tracker_cleaned.csv` once at process startup and serves
fast, read-only JSON over it (forecasting is the one exception: ARIMA on
~78 monthly points is genuinely sub-second, so that *is* computed
per-request). All the slow work lives in `scripts/refresh_data.py`, run on a
schedule by `.github/workflows/refresh-data.yml`.

**No API tokens required.** The primary source
(`scrape_layoffsfyi_airtable`'s shared-view path) captures a signed URL via
a one-time headless-browser visit (Playwright), then does a single plain,
unauthenticated `GET` — this is what produced the dataset currently
committed to this repo. `AIRTABLE_PAT`/`APIFY_TOKEN` are optional
faster-path/fallback enhancements the code tries first if set, never
required. If every live source fails, `refresh_data.py` exits non-zero and
the workflow's commit step never runs — the site keeps serving the last
known-good data instead of going stale silently or breaking.

## Running it locally

**Backend:**
```bash
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```
`FRONTEND_ORIGINS` (comma-separated) controls CORS; defaults to
`http://localhost:3000`. `DATA_DIR` defaults to `../data`.

> Note: on this project's dev machine, `uvicorn --reload`'s file watcher
> unreliably misses changes when the repo lives in a OneDrive-synced
> folder. If edits don't seem to take effect, restart the server manually.

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

**Refresh the data manually** (runs the same live scrape the scheduled job runs):
```bash
pip install -r requirements.txt
playwright install chromium
python scripts/refresh_data.py
```

## Deploying

- **Frontend → Vercel** (free/Hobby tier). Set the project's Root Directory
  to `frontend`, and `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.
- **Backend → Render** (free Web Service, no card required). This repo
  includes `render.yaml` — connect the repo as a Blueprint, or configure
  manually: root dir `backend`, build `pip install -r requirements.txt`,
  start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set
  `FRONTEND_ORIGINS` to your Vercel domain(s) once deployed.
  - **Known caveat:** Render's free tier sleeps after ~15 min idle; the
    first request after sleep costs a ~30–60s cold start (`pandas`/
    `statsmodels` import time included). Expected behavior, not a bug —
    don't fight it with a keep-alive pinger.
- **Scheduled refresh → GitHub Actions** (`.github/workflows/refresh-data.yml`,
  free for public repos). Trigger it once manually via `workflow_dispatch`
  to confirm the commit + Render's auto-deploy-on-push actually fire before
  relying on the daily cron.

## Known constraints (verified against the live internet, re-verify periodically)

- **The Apify actor fallback** (`useful-ai~tech-layoff-intelligence-tracker`)
  requires an `APIFY_TOKEN` (free tier at apify.com) and is only reached if
  the primary Airtable shared-view path fails.
- **WARN Act state filings** (final fallback, default Maryland DLLR) cover a
  single state and lack Stage/Country/AI-flag/funds-raised fields entirely
  — a refresh that falls all the way through to this source will show much
  smaller numbers and empty Stage/Country charts than the Airtable-sourced
  data. `pipeline/clean.py` guards every Airtable-only field on the source
  column actually being present, so this degrades gracefully rather than
  crashing.
- **Reason-tagging is deliberately naive** (keyword matching over article
  text, not real NLP) — intentional, so its limits stay visible instead of
  trusting a black box. Coverage compounds slowly across scheduled runs
  (`REASON_TAG_BATCH_SIZE`, default 50 articles/run) rather than all at once.
- **The ARIMA order is fixed, not auto-tuned**, to keep the model's
  assumptions visible and debuggable — `confidence_audit()` flags when a
  series has too little history for that fit to mean much.
- **`trueup.io/layoffs`** is a confirmed dead end for `requests`+BeautifulSoup
  (Cloudflare JS challenge) — not attempted by the production pipeline.

## Things to keep in mind when interpreting this data

- Is a spike in a sector/stage a real spike, or a base-rate artifact of that
  bucket having more companies tracked?
- Companies cite "restructuring" — does the data support that, or is it PR
  language masking something else?
- Is a forecast extrapolating a real trend, or continuing a few months of
  noise? What's *not* in the data that could break it?
