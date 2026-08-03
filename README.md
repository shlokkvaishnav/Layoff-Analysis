# Layoff Pulse 2026

A live scrape → clean → explore → forecast pipeline built for a DS Club
presentation to 2nd-year students. Every number shown comes from a live
network call at run time — there is no static CSV backing this project.

## Why this exists

Layoffs are continuous, heavily covered news — a live, scrapeable dataset
rather than a cleaned Kaggle CSV. The goal is to show what data science
actually looks like outside a tutorial: messy, ambiguous data that has to be
scraped, cleaned, and interrogated — and eventually used to make a claim
about the future — before any conclusion is trustworthy.

## Structure

```
layoff-pulse-2026/
├── scraper/
│   ├── tracker_scraper.py   # live: layoffs.fyi (Airtable) → Apify → WARN Act, with fallbacks
│   └── news_scraper.py      # live: RSS headlines + article text + naive reason-tagging
├── pipeline/
│   ├── clean.py             # fuzzy company dedupe, sector/date standardization, headcount imputation
│   ├── eda.py                # reusable Plotly chart functions
│   └── forecast.py          # naive rolling-avg baseline + ARIMA, with confidence intervals + audit
├── notebook/
│   └── layoff_pulse_2026.ipynb   # the presentation notebook (Colab-ready)
├── streamlit_app.py          # optional closing live dashboard demo
├── requirements.txt
└── data/
    ├── raw/                  # live scrape output lands here when run
    └── cleaned/               # cleaned output + final writeup lands here when run
```

## Running it (Colab — recommended for the presentation)

1. Open a new Colab notebook, or upload `notebook/layoff_pulse_2026.ipynb` directly.
2. The first cell clones this repo and installs dependencies — update the
   `git clone` URL to wherever you push this project.
3. Optionally set these as Colab secrets / env vars before running, for the
   fastest live-source path:
   - `LAYOFFSFYI_AIRTABLE_BASE` — find live in front of the audience via
     browser devtools (Network tab) on layoffs.fyi
   - `AIRTABLE_PAT` — only needed if the base isn't publicly readable
   - `APIFY_TOKEN` — free-tier token from apify.com, used as the fallback
     scraper if the Airtable path is locked down
   - `WARN_STATE_URL` — a direct URL to a state labor department's WARN
     notice listing (e.g. California EDD's WARN report page)
4. Run cells top to bottom. **Whatever happens live is the content** — if a
   source fails mid-demo, that's a legitimate teaching moment about scraper
   fragility, not a bug to hide.

## Running the Streamlit closing demo (local, not Colab)

```bash
pip install -r requirements.txt
export LAYOFFSFYI_AIRTABLE_BASE=... # optional
streamlit run streamlit_app.py
```

## Honest limitations (say these out loud during the presentation)

- **layoffs.fyi's Airtable view may or may not be publicly readable at
  presentation time** — websites change. `tracker_scraper.py` is written to
  fail loudly with a clear message and fall back automatically, rather than
  silently returning stale or fake data. If all three live sources fail
  during your actual run, that's worth narrating rather than papering over.
- **The reason-extraction step is deliberately naive** (keyword matching,
  not real NLP) — this is intentional so participants can see its limits
  rather than trust a black box.
- **The ARIMA order is fixed, not auto-tuned**, to keep the model's
  assumptions visible and debuggable live.
- **This was built and reviewed without live network access to layoffs.fyi,
  trueup.io, or news RSS feeds** (the development sandbox only allows
  package-registry domains). Test every scraper function against the real
  live internet before presenting — do not assume it works untested.

## Pedagogical checkpoint questions (embedded in the notebook, left unanswered)

**Descriptive:**
- Is the spike in a sector a real spike, or a base-rate artifact of that
  sector having more companies tracked?
- Companies cite "restructuring" — does the data support that, or is it PR
  language masking something else?
- What would a lazy analysis conclude here, and why would it be wrong?

**Predictive:**
- Is our forecast extrapolating a real trend, or just continuing a couple
  months of noise?
- What's NOT in our data that could break this forecast?
- If we're right, what should the data look like in 3 months? If we're wrong?
- Would you personally take a job offer in this sector based on this forecast?
