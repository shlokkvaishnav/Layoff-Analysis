"""
news_scraper.py
----------------
Live qualitative-data scraping: stated layoff reasons, exec quotes, and
follow-on hiring announcements from news coverage.

Uses RSS feeds (stable, server-rendered, no JS) rather than scraping
rendered article pages directly -- an intentional design choice worth
narrating live: "prefer the feed the publisher built for machines over
fighting the page they built for humans."

Nothing here is cached or static -- every call hits the live feed/page.
"""

import time
import requests
import feedparser
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LayoffPulse2026Bot/1.0; DS Club educational project)"}
REQUEST_TIMEOUT = 15

# A handful of layoff/restructuring-relevant keywords to search RSS titles for.
# Deliberately simple keyword matching (not sentiment ML) -- the pedagogy
# wants participants to SEE the limits of this approach and question it,
# not have it hidden behind a black-box classifier.
LAYOFF_KEYWORDS = [
    "layoff", "layoffs", "job cuts", "cuts jobs", "restructuring",
    "workforce reduction", "downsizing", "headcount reduction",
]

# Stated-reason phrases to flag when found in article text -- these are the
# raw phrases the checkpoint question asks participants to interrogate:
# does the data actually support them, or is this just PR language?
STATED_REASON_PHRASES = [
    "restructuring", "efficiency", "streamlin", "realign", "cost discipline",
    "AI", "automation", "macroeconomic", "market conditions", "right-sizing",
]

RSS_FEEDS = {
    "techcrunch": "https://techcrunch.com/feed/",
    "reuters_tech": "https://www.reutersagency.com/feed/?best-topics=tech",
}


def fetch_rss_layoff_headlines(feed_url: str, source_name: str) -> pd.DataFrame:
    """
    LIVE pull of an RSS feed, filtered to layoff-relevant headlines.

    Returns
    -------
    pd.DataFrame with columns: title, link, published, source
    """
    parsed = feedparser.parse(feed_url)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"Could not parse feed {feed_url}: {parsed.bozo_exception}")

    rows = []
    for entry in parsed.entries:
        title = entry.get("title", "")
        if any(kw.lower() in title.lower() for kw in LAYOFF_KEYWORDS):
            rows.append({
                "title": title,
                "link": entry.get("link"),
                "published": entry.get("published", entry.get("updated")),
                "source": source_name,
                "_scraped_at": datetime.utcnow().isoformat(),
            })

    return pd.DataFrame(rows)


def fetch_all_feeds() -> pd.DataFrame:
    """Pull every configured RSS feed live and concatenate layoff-relevant headlines."""
    frames = []
    for name, url in RSS_FEEDS.items():
        try:
            print(f"Fetching {name} RSS (live)...")
            df = fetch_rss_layoff_headlines(url, name)
            print(f"  {len(df)} layoff-relevant headlines found.")
            frames.append(df)
        except Exception as e:
            print(f"  Failed: {e}")
        time.sleep(0.5)

    if not frames:
        return pd.DataFrame(columns=["title", "link", "published", "source"])
    return pd.concat(frames, ignore_index=True)


def extract_article_text(url: str) -> str:
    """
    LIVE fetch of a single article's full text (best-effort). Grabs all
    <p> tags -- crude but transparent, which is the point: participants
    should see exactly how little "extraction" here really does, so they
    don't over-trust the reason-tagging step downstream.
    """
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    return " ".join(paragraphs)


def tag_stated_reasons(article_text: str) -> list:
    """
    Crude keyword tagging of which stated-reason phrases appear in an
    article's text. This is intentionally naive -- the checkpoint question
    ("does the data support 'restructuring', or is it PR language?") only
    works pedagogically if participants can see this is just string
    matching, not real NLP understanding of causality.
    """
    text_lower = article_text.lower()
    return [phrase for phrase in STATED_REASON_PHRASES if phrase.lower() in text_lower]


def build_news_context_table(headlines_df: pd.DataFrame, max_articles: int = 15) -> pd.DataFrame:
    """
    For a sample of scraped headlines, fetch full article text live and tag
    stated reasons. Capped at max_articles to keep the live demo fast --
    call this out explicitly ("we're sampling, not exhaustively scraping,
    because live demo time is finite" is itself a real DS tradeoff).
    """
    sample = headlines_df.head(max_articles).copy()
    reasons_col = []
    for _, row in sample.iterrows():
        try:
            text = extract_article_text(row["link"])
            reasons_col.append(tag_stated_reasons(text))
        except Exception as e:
            reasons_col.append([f"fetch_failed: {e}"])
        time.sleep(0.5)
    sample["stated_reasons_found"] = reasons_col
    return sample


if __name__ == "__main__":
    print("=== Layoff Pulse 2026: live news scrape demo ===\n")
    headlines = fetch_all_feeds()
    print(f"\nTotal layoff-relevant headlines across feeds: {len(headlines)}")
    if not headlines.empty:
        context = build_news_context_table(headlines, max_articles=10)
        print(context[["title", "source", "stated_reasons_found"]])
        context.to_csv("../data/raw/news_context_live.csv", index=False)
