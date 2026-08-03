"""
streamlit_app.py
-----------------
Optional closing demo: a live-refreshing dashboard version of the pipeline,
run once at the end of the presentation as the "this is what production DS
tooling looks like" finale. Not the main teaching vehicle -- the notebook is.

Run with:
    streamlit run streamlit_app.py
"""

import sys
import os
import streamlit as st
import pandas as pd

sys.path.append("scraper")
sys.path.append("pipeline")

import tracker_scraper as ts
import clean as cl
import eda
import forecast as fc

st.set_page_config(page_title="Layoff Pulse 2026", layout="wide")
st.title("🔴 Layoff Pulse 2026 — Live Dashboard")
st.caption("Every number on this page was scraped live when the page loaded. Refresh to re-scrape.")

with st.spinner("Scraping live tracker data..."):
    try:
        raw_df = ts.get_live_tracker_data(
            airtable_base_id=os.environ.get("LAYOFFSFYI_AIRTABLE_BASE"),
            warn_state_url=os.environ.get("WARN_STATE_URL"),
        )
        cleaned_df = cl.clean_tracker_dataframe(raw_df)
    except Exception as e:
        st.error(f"Live scrape failed this run: {e}")
        st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Total Reported Layoffs (rows)", len(cleaned_df))
col2.metric("People Affected (sum)", int(cleaned_df["laid_off"].sum()))
col3.metric("Rows with Imputed Headcount", int(cleaned_df["_headcount_imputed"].sum()))

st.subheader("Monthly Trend")
st.plotly_chart(eda.plot_monthly_trend(cleaned_df), use_container_width=True)

st.subheader("By Sector (vs. Companies Tracked)")
st.plotly_chart(eda.plot_by_sector(cleaned_df), use_container_width=True)

st.subheader("Forecast")
sectors = cleaned_df.groupby("sector")["laid_off"].sum().sort_values(ascending=False).head(6).index.tolist()
sector = st.selectbox("Sector", sectors)
horizon = st.slider("Forecast horizon (months)", 1, 6, 3)

series = fc.prepare_monthly_series(cleaned_df, sector)
naive_fc = fc.naive_baseline_forecast(series, horizon=horizon)
try:
    arima_fc = fc.arima_forecast(series, horizon=horizon)
except ValueError as e:
    st.warning(f"ARIMA skipped: {e}")
    arima_fc = naive_fc.copy()
    arima_fc["model"] = "ARIMA_unavailable_fallback_to_naive"

st.plotly_chart(fc.plot_forecast_comparison(series, naive_fc, arima_fc, sector), use_container_width=True)

st.subheader("Confidence Audit")
audit = fc.confidence_audit(series, sector)
for a in audit["assumptions"]:
    st.write(f"**[{a['risk_level']}]** {a['assumption']}  \n*shaky if: {a['shaky_if']}*")
