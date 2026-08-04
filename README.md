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

All of the below were verified against the real live internet on
**2026-08-03** — not speculation. Re-verify closer to your actual
presentation date, since every one of these is a moving target by design.

- **layoffs.fyi's public Airtable REST API is locked, but there's a real
  working path anyway — an update from 2026-08-04.** The base id
  (`app1PaujS9zxVGUZ4`) is real and auto-discoverable from layoffs.fyi's
  page-source HTML, but every request to Airtable's *public* REST API
  against it returns `401 AUTHENTICATION_REQUIRED`, PAT or not — that base
  is genuinely locked down for that API. However, the embed page itself
  doesn't use that public API at all: it calls Airtable's internal,
  unauthenticated "shared view" endpoint
  (`airtable.com/v0.3/view/<viewId>/readSharedViewData`) to render the
  public embed. `scrape_layoffsfyi_airtable()` now captures that endpoint's
  signed request live (one-time headless-browser visit via Playwright,
  since the signature is issued client-side per page load) and replays it
  with plain `requests` — confirmed live: **4,545 real rows, real columns
  (Company, Location HQ, # Laid Off, Date, Industry, Source, Stage, $
  Raised (mm), Country, AI-flag), history back to March 2020**, no API key
  needed. Requires `pip install playwright && playwright install
  chromium`. If this ever breaks (Airtable could change the signing scheme
  or layoffs.fyi could swap embed providers), it's a good live moment —
  the code raises a clear `RuntimeError` and the pipeline falls through to
  Apify, then WARN Act, same as before.
- **The Apify actor (`useful-ai~tech-layoff-intelligence-tracker`) is real,
  public, and active** — 712 successful runs in the last 30 days per its
  public store listing, most recently run the same day this was checked.
  It correctly requires an `APIFY_TOKEN` (401 `token-not-provided` without
  one); the free tier's exact monthly compute-unit limits are set at the
  Apify account level and weren't verified here, since that requires
  creating an account — check apify.com's current free-tier terms before
  presenting.
- **California EDD's WARN page no longer has the notice listing as an HTML
  table** — an earlier obvious pick for `scrape_warn_act()`'s default. Its
  actual data now ships as XLSX/PDF downloads; the one `<table>` still on
  the page is an unrelated legal-provisions comparison chart. The old
  "grab the largest `<table>`" heuristic would have silently parsed that
  wrong table instead of failing — `scrape_warn_act()` now validates that
  the chosen table's headers look WARN-notice-shaped (company/employer +
  date columns) before accepting it, and raises otherwise. The default
  state URL was switched to **Maryland DLLR**
  (`https://www.dllr.state.md.us/employment/warn.shtml`), which does still
  serve a genuine server-rendered table (85 real notices as of the last
  check) — but Maryland's real column names are `Company`, `Notice Date`,
  `Total  Employees` (note the double space, an artifact of collapsed
  `<br>` tags), not `company`/`date`/`laid_off`, and WARN filings report a
  NAICS code, not a marketing-style sector, so `clean_tracker_dataframe()`
  is called with an explicit column map depending on which source actually
  succeeded (see `pipeline/clean.py`'s `__main__` block and the notebook's
  section 3).
- **trueup.io/layoffs is a genuine, confirmed dead end for
  requests+BeautifulSoup**, not a bug to fix: it's behind a Cloudflare JS
  challenge ("Just a moment...") that returns 403 to every plain HTTP
  request regardless of User-Agent/Accept headers, because passing it
  requires executing JS. `scrape_trueup_headline()` now raises a
  `RuntimeError` that says exactly this, instead of an opaque
  `HTTPError`. Getting real data out of this source would require a
  headless browser (Playwright/Selenium), which this project deliberately
  avoids — a fine live talking point about the limits of "just use
  requests."
- **TechCrunch's RSS feed (`techcrunch.com/feed/`) still resolves and
  parses cleanly.** The originally-planned Reuters feed
  (`reutersagency.com/feed/?best-topics=tech`) is dead — that domain is now
  a corporate agency-services site with no such feed (404), and the
  obvious alternative (`reuters.com/technology/rss`) is blocked by a
  bot-detection challenge that requires JS (401). Swapped in CNBC's
  Technology RSS feed instead, which resolved fine and covers layoffs
  regularly. On any given day, though, expect **zero** layoff-relevant
  headlines in the top ~20-30 items of either feed — that's not a bug, it's
  the real limit of a simple keyword filter over a general tech feed rather
  than a dedicated layoffs feed.
- **`pd.read_html()` requires an `io.StringIO` wrapper on current pandas**
  (3.x) — passing a raw HTML string directly now raises an `OSError`
  ("Error reading file") because pandas treats a bare string as a
  filepath/URL rather than markup. Fixed in `scrape_warn_act()`.
- **The reason-extraction step is deliberately naive** (keyword matching,
  not real NLP) — this is intentional so participants can see its limits
  rather than trust a black box.
- **The ARIMA order is fixed, not auto-tuned**, to keep the model's
  assumptions visible and debuggable live. Confirmed to fit successfully on
  real WARN Act data (7 months of history, right at ARIMA's practical
  minimum) — with only 7 months, treat the resulting confidence interval as
  illustrative, not precise; the code's own `confidence_audit()` flags this.

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
