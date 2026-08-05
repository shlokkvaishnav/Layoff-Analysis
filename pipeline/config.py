"""
config.py
---------
Centralized configuration for the pipeline package. Values default to what
was previously hardcoded in clean.py, overridable via environment variables.
"""

import logging
import os

# Default fuzzy-match threshold for dedupe_company_names() -- see
# pipeline/clean.py. Kept as a function default parameter too, so callers
# can still override it per-call; this just sets the shared default.
DEDUPE_THRESHOLD = int(os.environ.get("DEDUPE_THRESHOLD", "85"))

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
