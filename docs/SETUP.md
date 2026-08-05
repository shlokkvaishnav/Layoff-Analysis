# Local Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/) via the root
`pyproject.toml` / `uv.lock` (`pip install uv` if you don't have it).

## Backend

```bash
uv sync
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Env vars (both optional): `FRONTEND_ORIGINS` (comma-separated, controls
CORS, defaults to `http://localhost:3000`), `DATA_DIR` (defaults to
`../data`).

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

## Refreshing the data manually

Runs the same scrape → clean → tag pipeline the scheduled job runs:

```bash
uv sync
uv run playwright install chromium
uv run python scripts/refresh_data.py
```

No API tokens are required for this to work end to end. Optional env
vars for the faster/fallback paths: `AIRTABLE_PAT`, `LAYOFFSFYI_AIRTABLE_BASE`,
`APIFY_TOKEN`, `WARN_STATE_URL`. `REASON_TAG_BATCH_SIZE` (default 50)
caps how many new articles get tagged per run.

## Tests

```bash
uv run python -m pytest backend/tests/ -v
```

```bash
cd frontend
npm run lint
npm run build
```
