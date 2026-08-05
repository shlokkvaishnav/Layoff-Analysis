"""
config.py
---------
Centralized configuration for the scraper package. Values default to what
was previously hardcoded across tracker_scraper.py / news_scraper.py, but
are now overridable via environment variables for production deployments
(CI runners, Render) without code changes.
"""

import logging
import os

USER_AGENT = os.environ.get(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (compatible; LayoffPulse2026Bot/1.0; DS Club educational project)",
)
HEADERS = {"User-Agent": USER_AGENT}

# tracker_scraper.py's live network calls (Airtable/Apify/WARN) vs.
# news_scraper.py's RSS/article fetches get separate timeouts since they're
# different concerns with different historical defaults (30s vs 15s).
REQUEST_TIMEOUT = int(os.environ.get("SCRAPER_REQUEST_TIMEOUT", "30"))
NEWS_REQUEST_TIMEOUT = int(os.environ.get("NEWS_REQUEST_TIMEOUT", "15"))

# Confirmed live 2026-08-03: a state WARN page with a genuine server-rendered
# HTML table of individual notices -- see tracker_scraper.scrape_warn_act().
DEFAULT_WARN_STATE_URL = os.environ.get(
    "WARN_STATE_URL", "https://www.dllr.state.md.us/employment/warn.shtml"
)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False
    return logger
