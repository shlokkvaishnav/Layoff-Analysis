"""
tracker_scraper.py
-------------------
Live structured-data scraping for the Layoff Pulse 2026 pipeline.

Teaching point for the audience: real scraping targets are moving targets.
This module tries THREE live sources, in order of speed/reliability, and
falls back gracefully instead of crashing the live demo:

    1. layoffs.fyi's embedded Airtable view  (fastest, no JS render needed)
    2. Apify's hosted "Tech Layoff Intelligence Tracker" actor (paid/free-tier API)
    3. WARN Act state filing pages (official, server-rendered HTML)

Nothing here reads from a static CSV. Every function makes a real network
call at run time. If a source's structure has changed since this was written
(which WILL happen -- that's the point), the function raises a clear,
narratable error instead of silently returning garbage.

Run this file directly during the demo to see raw, messy, live output:
    python tracker_scraper.py
"""

import os
import re
import time
import json
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = "Mozilla/5.0 (compatible; LayoffPulse2026Bot/1.0; DS Club educational project)"
HEADERS = {"User-Agent": USER_AGENT}
REQUEST_TIMEOUT = 30

# Confirmed live 2026-08-03: a state WARN page with a genuine server-rendered
# HTML table of individual notices (not just a PDF/XLSX download, which is
# what CA EDD's page moved to -- see scrape_warn_act() docstring).
DEFAULT_WARN_STATE_URL = "https://www.dllr.state.md.us/employment/warn.shtml"

# ---------------------------------------------------------------------------
# 1. layoffs.fyi -> embedded Airtable view
# ---------------------------------------------------------------------------

def _discover_airtable_base_id() -> str:
    """
    Auto-discover the Airtable base id embedded in layoffs.fyi's homepage
    HTML. Confirmed live 2026-08-03: the id is sitting in plain page source
    as an `airtable.com/embed/appXXXXXXXXXXXXXX/...` link -- no devtools
    Network-tab digging required, just a regex over the raw HTML. Kept as a
    live call (not hardcoded) since this is exactly the kind of thing that
    silently rots: if layoffs.fyi swaps embed providers, this raises instead
    of returning a stale id.
    """
    resp = requests.get("https://layoffs.fyi/", headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    match = re.search(r"airtable\.com/embed/(app[a-zA-Z0-9]{14})", resp.text)
    if not match:
        raise RuntimeError(
            "Could not find an Airtable base id embedded in layoffs.fyi's "
            "homepage HTML -- the page may have swapped embed providers or "
            "moved to JS-only rendering since this was last checked."
        )
    return match.group(1)


def scrape_layoffsfyi_airtable(base_id: str = None, table_name: str = "Layoffs") -> pd.DataFrame:
    """
    Attempt a LIVE pull from the Airtable base backing layoffs.fyi's table.

    layoffs.fyi's on-page table links out to an embedded Airtable view. If
    that view (or a base_id you've found via browser devtools -> Network tab)
    is publicly readable, this hits Airtable's real REST API directly --
    no Selenium, no HTML parsing, just clean JSON.

    Confirmed live 2026-08-03: the base id (currently 'app1PaujS9zxVGUZ4') is
    real and auto-discoverable straight from layoffs.fyi's HTML (see
    _discover_airtable_base_id()), but Airtable's REST API returns
    401 AUTHENTICATION_REQUIRED on every table/table-id tried against it
    without a Personal Access Token -- the base is not publicly readable.
    The embed HTML itself also renders client-side (no records inline in
    the page source), so there's no static-HTML shortcut either; a PAT (or
    falling back to Apify/WARN Act) is genuinely required.

    Parameters
    ----------
    base_id : str
        Airtable base id (looks like 'appXXXXXXXXXXXXXX'). If omitted, this
        is auto-discovered live from layoffs.fyi's homepage HTML (falling
        back to the LAYOFFSFYI_AIRTABLE_BASE env var if discovery fails).
    table_name : str
        Table name or id within the base.

    Returns
    -------
    pd.DataFrame
        Raw (uncleaned) records. Raises RuntimeError with a clear message
        if the base isn't publicly readable -- this is expected and should
        be narrated live, not treated as a bug.
    """
    base_id = base_id or os.environ.get("LAYOFFSFYI_AIRTABLE_BASE")
    if not base_id:
        try:
            base_id = _discover_airtable_base_id()
            print(f"      (auto-discovered Airtable base id: {base_id})")
        except Exception as e:
            raise RuntimeError(
                f"No Airtable base_id supplied and auto-discovery failed ({e}). "
                "Find it live: open layoffs.fyi, click through to the embedded "
                "Airtable view, open browser devtools -> Network tab, filter "
                "for 'airtable.com', and copy the appXXXXXXXXXXXXXX id from "
                "the request URL."
            )

    pat = os.environ.get("AIRTABLE_PAT")  # optional Personal Access Token

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    req_headers = dict(HEADERS)
    if pat:
        req_headers["Authorization"] = f"Bearer {pat}"

    records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers=req_headers, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401 or resp.status_code == 403:
            raise RuntimeError(
                f"Airtable base '{base_id}' requires authentication "
                f"(status {resp.status_code}). Set AIRTABLE_PAT env var, "
                "or fall back to scrape_via_apify() / scrape_warn_act()."
            )
        resp.raise_for_status()
        payload = resp.json()
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            break
        time.sleep(0.2)  # be polite to the API

    if not records:
        raise RuntimeError("Airtable base returned zero records -- table name or schema may have changed.")

    df = pd.json_normalize([r.get("fields", {}) for r in records])
    df["_source"] = "layoffs.fyi (Airtable, live)"
    df["_scraped_at"] = datetime.now(timezone.utc).isoformat()
    return df


# ---------------------------------------------------------------------------
# 2. Apify hosted actor fallback
# ---------------------------------------------------------------------------

def scrape_via_apify(actor_id: str = "useful-ai~tech-layoff-intelligence-tracker") -> pd.DataFrame:
    """
    LIVE fallback: run Apify's hosted layoffs.fyi scraper actor and pull
    its dataset. Requires an Apify API token (free tier available) set as
    the APIFY_TOKEN environment variable.

    This is still a live scrape -- the actor itself hits layoffs.fyi fresh
    on each run -- we're just outsourcing the "keep the parser working"
    maintenance burden to Apify instead of owning it ourselves.
    """
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError(
            "No APIFY_TOKEN set. Get a free-tier token at apify.com, then "
            "export APIFY_TOKEN=... before calling this function."
        )

    # run-sync-get-dataset-items blocks until the actor finishes an actual
    # live scrape of layoffs.fyi, which routinely takes well over a minute --
    # confirmed live: a 60s client timeout fires before the actor is done,
    # which looks like a network failure but is really just "didn't wait
    # long enough." Apify's own default actor timeout is up to 300s, so the
    # client timeout needs headroom beyond that.
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    try:
        resp = requests.post(run_url, params={"token": token, "timeout": 300}, timeout=320)
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Apify actor run timed out client-side after 300s. The actor "
            "may be slow/queued on Apify's end right now -- check the run's "
            "status at https://console.apify.com/ or fall back to "
            "scrape_warn_act()."
        )
    resp.raise_for_status()
    items = resp.json()

    if not items:
        raise RuntimeError("Apify actor returned no items -- check actor_id or quota.")

    df = pd.DataFrame(items)
    df["_source"] = "layoffs.fyi (via Apify actor, live)"
    df["_scraped_at"] = datetime.now(timezone.utc).isoformat()
    return df


# ---------------------------------------------------------------------------
# 3. WARN Act state filings (official, server-rendered)
# ---------------------------------------------------------------------------

def scrape_warn_act(state_url: str = DEFAULT_WARN_STATE_URL) -> pd.DataFrame:
    """
    LIVE scrape of a single state's WARN Act notice listing page using
    requests + BeautifulSoup (no JS rendering needed -- these are usually
    plain server-rendered HTML tables).

    Confirmed live 2026-08-03: California EDD's WARN page (an earlier
    obvious pick) has moved its actual notice data to XLSX/PDF downloads --
    the only <table> left on that page is an unrelated legal-provisions
    comparison table, which the old "just take the largest table" heuristic
    would have silently accepted as real data. Maryland DLLR's WARN page
    (the default here) still serves a genuine server-rendered HTML table of
    individual notices, so it's used as the default demo URL. To guard
    against the CA-style failure mode for whichever URL you pass in, the
    chosen table's headers are checked for WARN-notice-shaped column names
    before being accepted.

    Parameters
    ----------
    state_url : str
        Direct URL to a state labor department's WARN notice listing.
        Defaults to Maryland DLLR's page; pass a different one live so the
        audience sees you picking a real state page and inspecting its
        table structure before writing the parser.

    Returns
    -------
    pd.DataFrame
        Raw WARN notice rows: company, location, effective date, employees
        affected -- schema varies by state, which is itself a cleaning
        problem you'll hit in pipeline/clean.py.
    """
    from bs4 import BeautifulSoup
    from io import StringIO

    resp = requests.get(state_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        raise RuntimeError(
            f"No <table> elements found at {state_url}. The state may have "
            "switched to a JS-rendered dashboard -- narrate this live as an "
            "example of a source going stale mid-project."
        )

    # Consider tables largest-first, but only accept one whose header row
    # actually looks like a WARN notice listing (company/employer + a date
    # column) -- otherwise we risk silently parsing an unrelated table on
    # the page (confirmed to happen on CA EDD's page, which still has one
    # <table> that's just a legal-provisions comparison chart).
    warn_shape_keywords = ("company", "employer", "notice", "date", "employee")
    for target_table in sorted(tables, key=lambda t: len(t.find_all("tr")), reverse=True):
        df = pd.read_html(StringIO(str(target_table)))[0]
        headers = " ".join(str(c) for c in df.columns).lower()
        if any(kw in headers for kw in warn_shape_keywords) and len(df) > 1:
            df["_source"] = f"WARN Act ({state_url})"
            df["_scraped_at"] = datetime.now(timezone.utc).isoformat()
            return df

    raise RuntimeError(
        f"Found {len(tables)} <table> element(s) at {state_url}, but none had "
        "headers that look like a WARN notice listing (expected something "
        "like company/employer + date columns). The page structure has "
        "likely changed -- narrate this live as a source going stale."
    )


# ---------------------------------------------------------------------------
# 4. TrueUp.io aggregate headline stats (for the opening "big number" hook)
# ---------------------------------------------------------------------------

def scrape_trueup_headline() -> dict:
    """
    LIVE scrape of TrueUp.io's /layoffs page for the year-to-date headline
    numbers (total layoffs, people affected, per-day rate). Plain requests +
    BeautifulSoup -- used for the opening hook slide, not the full dataset.

    Confirmed live 2026-08-03: trueup.io sits behind a Cloudflare JS
    challenge ("Just a moment...") -- every plain-requests attempt gets a
    403 regardless of User-Agent/Accept headers, because the check requires
    executing JS to solve, which requests/BeautifulSoup can't do. This is a
    genuine dead end for this approach (would need a headless browser like
    Playwright to get past it), not a bug in the parsing logic below.
    """
    from bs4 import BeautifulSoup

    try:
        resp = requests.get("https://www.trueup.io/layoffs", headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"trueup.io/layoffs returned {resp.status_code}. As of the last "
            "check (2026-08-03) this site is behind a Cloudflare JS "
            "challenge that blocks plain requests entirely -- getting past "
            "it would require a headless browser (e.g. Playwright), which "
            "this module deliberately doesn't use. Treat this as a real, "
            "documented dead end, not a parsing bug."
        ) from e

    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)

    # Structure is prose-like, not a clean table -- pull numbers with a
    # tolerant regex rather than assuming fixed HTML tags (a good live
    # talking point: "sometimes the parser IS the regex").
    numbers = re.findall(r"[\d,]+", text)
    return {
        "_source": "trueup.io (live)",
        "_scraped_at": datetime.now(timezone.utc).isoformat(),
        "raw_numbers_found": numbers[:10],  # hand these to the audience to sanity-check
        "raw_text_snippet": text[:500],
    }


# ---------------------------------------------------------------------------
# Orchestrator: try sources in order, log what happened, never fully die
# ---------------------------------------------------------------------------

def get_live_tracker_data(airtable_base_id: str = None, warn_state_url: str = DEFAULT_WARN_STATE_URL) -> pd.DataFrame:
    """
    Try each live source in order of speed/reliability. Prints what it tried
    and why it moved on -- this narration IS the pedagogical content, so it
    intentionally is not silenced.

    Confirmed live 2026-08-03: with no AIRTABLE_PAT or APIFY_TOKEN set,
    sources 1 and 2 both fail predictably with clean 401-derived
    RuntimeErrors (see their docstrings), and source 3 (WARN Act, defaulting
    to Maryland DLLR) is the one that actually succeeds end-to-end -- this
    is the realistic fallback path for an unauthenticated demo run.
    """
    attempts = []

    try:
        print("[1/3] Trying layoffs.fyi Airtable view (live)...")
        df = scrape_layoffsfyi_airtable(base_id=airtable_base_id)
        print(f"      Success -- {len(df)} rows.")
        return df
    except Exception as e:
        print(f"      Failed: {e}")
        attempts.append(("airtable", str(e)))

    try:
        print("[2/3] Trying Apify hosted actor (live)...")
        df = scrape_via_apify()
        print(f"      Success -- {len(df)} rows.")
        return df
    except Exception as e:
        print(f"      Failed: {e}")
        attempts.append(("apify", str(e)))

    if warn_state_url:
        try:
            print("[3/3] Trying WARN Act state filing page (live)...")
            df = scrape_warn_act(warn_state_url)
            print(f"      Success -- {len(df)} rows.")
            return df
        except Exception as e:
            print(f"      Failed: {e}")
            attempts.append(("warn_act", str(e)))

    raise RuntimeError(
        "All live sources failed this run. Attempts: "
        f"{json.dumps(attempts, indent=2)}\n"
        "This is a legitimate outcome to show live -- it demonstrates why "
        "production scrapers need monitoring and multiple fallbacks."
    )


if __name__ == "__main__":
    print("=== Layoff Pulse 2026: live tracker scrape demo ===\n")
    try:
        hook = scrape_trueup_headline()
        print("Opening hook numbers (raw, unparsed):", hook["raw_numbers_found"], "\n")
    except RuntimeError as e:
        print(f"Opening hook failed (documented dead end -- narrate live): {e}\n")

    df = get_live_tracker_data(
        airtable_base_id=os.environ.get("LAYOFFSFYI_AIRTABLE_BASE"),
        warn_state_url=os.environ.get("WARN_STATE_URL", DEFAULT_WARN_STATE_URL),
    )
    print("\nRaw live sample (first 5 rows):")
    print(df.head())

    from pathlib import Path
    out_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / "tracker_raw_live.csv"
    df.to_csv(out_file, index=False)
    print(f"\nSaved to {out_file}")
