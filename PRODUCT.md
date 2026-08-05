# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) + TypeScript + Tailwind CSS + Recharts, calling a FastAPI backend. Existing codebase (not greenfield) -- see frontend/ and backend/.

## Users

Investors and market/industry analysts tracking tech-sector layoffs as a market signal are this landing page's primary visitor; job seekers, researchers, and journalists use the same underlying data secondarily via the dashboard itself. The landing page's call to action leads into the live dashboard (/trend).

## Product Purpose

Layoff Pulse 2026 answers three questions about tech-sector layoffs from live-scraped, continuously-refreshed data: what's the trend, what reason do companies give, and what does that imply about the future (forecast). Sector/industry alone turned out to be a weak lens for this data (the largest "sector" by headcount is an uninformative "Other" catch-all) -- funding Stage and Country are more reliable structured dimensions, and stated reasons are extracted directly from each layoff's own linked news source rather than assumed.

## Positioning

Not a static, one-time dataset (e.g. a Kaggle CSV) -- the underlying data refreshes on a schedule from live sources (primarily layoffs.fyi), with a naive-but-transparent reason-extraction method and an ARIMA-based forecast that ships its own confidence-audit of assumptions rather than presenting a number without caveats.

## Operating Context

The dashboard (/trend, /sector, /reasons, /forecast, /raw) is the actual product; this landing page is a marketing/entry surface pointing into it. Data refreshes once daily via a scheduled job; the site is not real-time.

## Capabilities and Constraints

- Real, live stats available from the backend API: total rows tracked, total people affected (sum), distinct companies tracked, and a last-refreshed timestamp + source (via `/api/meta/summary` and `/api/meta/freshness`).
- No user accounts, no paid tiers, no real customer testimonials or logos exist -- none may be fabricated.
- No A/B testing infrastructure exists or is planned for this surface (explicitly out of scope, confirmed with the user).

## Brand Commitments

Name: "Layoff Pulse 2026". The existing dashboard's visual language uses a warm brown/creme palette (`frontend/src/app/globals.css`, `frontend/src/lib/colors.ts`) -- CSS variables `--accent` (#8B5A2B light / #D2B48C dark), `--background`, `--foreground`, `--card`, `--border`, with light/dark theme toggled via a `data-theme` attribute.

## Evidence on Hand

Real, live data via the backend API (not fabricated): row counts, people-affected totals, distinct company counts, data source name, last-refresh timestamp. No testimonials, press mentions, or customer logos exist -- none may be invented.

## Product Principles

- Every number shown must be real and traceable to the live API -- no placeholder/fake stats, no fabricated social proof.
- This is also a portfolio piece built to demonstrate engineering and design craft to an interviewer -- craft quality matters as much as function.
- Stay within the scope already planned for this surface: hero + real-stats credibility section + CTA into the dashboard.

## Accessibility & Inclusion

The existing dashboard already supports light/dark theme via a toggle; the landing page should honor the same theme system rather than introducing a separate one.
