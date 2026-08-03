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
import time
import json
import requests
import pandas as pd
from datetime import datetime

USER_AGENT = "Mozilla/5.0 (compatible; LayoffPulse2026Bot/1.0; DS Club educational project)"
HEADERS = {"User-Agent": USER_AGENT}
REQUEST_TIMEOUT = 15


# ---------------------------------------------------------------------------
# 1. layoffs.fyi -> embedded Airtable view
# ---------------------------------------------------------------------------

def scrape_layoffsfyi_airtable(base_id: str = None, table_name: str = "Layoffs") -> pd.DataFrame:
    """
    Attempt a LIVE pull from the Airtable base backing layoffs.fyi's table.

    layoffs.fyi's on-page table links out to an embedded Airtable view. If
    that view (or a base_id you've found via browser devtools -> Network tab)
    is publicly readable, this hits Airtable's real REST API directly --
    no Selenium, no HTML parsing, just clean JSON.

    Parameters
    ----------
    base_id : str
        Airtable base id (looks like 'appXXXXXXXXXXXXXX'). Find it live in
        front of the audience via browser devtools on layoffs.fyi -- this is
        itself a good "here's how you actually find where the data lives"
        demo moment. Can also be set via the LAYOFFSFYI_AIRTABLE_BASE env var.
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
    pat = os.environ.get("AIRTABLE_PAT")  # optional Personal Access Token

    if not base_id:
        raise RuntimeError(
            "No Airtable base_id supplied. Find it live: open layoffs.fyi, "
            "click through to the embedded Airtable view, open browser "
            "devtools -> Network tab, filter for 'airtable.com', and copy "
            "the appXXXXXXXXXXXXXX id from the request URL."
        )

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
    df["_scraped_at"] = datetime.utcnow().isoformat()
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

    run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    resp = requests.get(run_url, params={"token": token}, timeout=60)
    resp.raise_for_status()
    items = resp.json()

    if not items:
        raise RuntimeError("Apify actor returned no items -- check actor_id or quota.")

    df = pd.DataFrame(items)
    df["_source"] = "layoffs.fyi (via Apify actor, live)"
    df["_scraped_at"] = datetime.utcnow().isoformat()
    return df


# ---------------------------------------------------------------------------
# 3. WARN Act state filings (official, server-rendered)
# ---------------------------------------------------------------------------

def scrape_warn_act(state_url: str) -> pd.DataFrame:
    """
    LIVE scrape of a single state's WARN Act notice listing page using
    requests + BeautifulSoup (no JS rendering needed -- these are usually
    plain server-rendered HTML tables, e.g. California EDD's WARN report).

    Parameters
    ----------
    state_url : str
        Direct URL to a state labor department's WARN notice listing.
        Pass this in live so the audience sees you picking a real state
        page (e.g. California EDD WARN report) and inspecting its table
        structure before writing the parser.

    Returns
    -------
    pd.DataFrame
        Raw WARN notice rows: company, location, effective date, employees
        affected -- schema varies by state, which is itself a cleaning
        problem you'll hit in pipeline/clean.py.
    """
    from bs4 import BeautifulSoup

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

    # Take the largest table on the page as the notice listing
    target_table = max(tables, key=lambda t: len(t.find_all("tr")))
    df = pd.read_html(str(target_table))[0]
    df["_source"] = f"WARN Act ({state_url})"
    df["_scraped_at"] = datetime.utcnow().isoformat()
    return df


# ---------------------------------------------------------------------------
# 4. TrueUp.io aggregate headline stats (for the opening "big number" hook)
# ---------------------------------------------------------------------------

def scrape_trueup_headline() -> dict:
    """
    LIVE scrape of TrueUp.io's /layoffs page for the year-to-date headline
    numbers (total layoffs, people affected, per-day rate). Plain requests +
    BeautifulSoup -- used for the opening hook slide, not the full dataset.
    """
    from bs4 import BeautifulSoup
    import re

    resp = requests.get("https://www.trueup.io/layoffs", headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)

    # Structure is prose-like, not a clean table -- pull numbers with a
    # tolerant regex rather than assuming fixed HTML tags (a good live
    # talking point: "sometimes the parser IS the regex").
    numbers = re.findall(r"[\d,]+", text)
    return {
        "_source": "trueup.io (live)",
        "_scraped_at": datetime.utcnow().isoformat(),
        "raw_numbers_found": numbers[:10],  # hand these to the audience to sanity-check
        "raw_text_snippet": text[:500],
    }


# ---------------------------------------------------------------------------
# Orchestrator: try sources in order, log what happened, never fully die
# ---------------------------------------------------------------------------

def get_live_tracker_data(airtable_base_id: str = None, warn_state_url: str = None) -> pd.DataFrame:
    """
    Try each live source in order of speed/reliability. Prints what it tried
    and why it moved on -- this narration IS the pedagogical content, so it
    intentionally is not silenced.
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
    hook = scrape_trueup_headline()
    print("Opening hook numbers (raw, unparsed):", hook["raw_numbers_found"], "\n")

    df = get_live_tracker_data(
        airtable_base_id=os.environ.get("LAYOFFSFYI_AIRTABLE_BASE"),
        warn_state_url=os.environ.get("WARN_STATE_URL"),
    )
    print("\nRaw live sample (first 5 rows):")
    print(df.head())
    df.to_csv("../data/raw/tracker_raw_live.csv", index=False)
