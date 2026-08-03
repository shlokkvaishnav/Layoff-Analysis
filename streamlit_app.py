"""
streamlit_app.py
-----------------
Advanced Live-Refreshing Dashboard Version of the Layoff Pulse Pipeline.
Run with:
    streamlit run streamlit_app.py
"""

import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd

sys.path.append("scraper")
sys.path.append("pipeline")

import tracker_scraper as ts
import news_scraper as ns
import clean as cl
import eda
import forecast as fc

st.set_page_config(page_title="Layoff Pulse 2026", layout="wide")

# ---------------------------------------------------------------------
# Sidebar - Data Fetching & News
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Data Configuration")
    st.caption("Load local CSV instantly, or scrape live data in the background.")
    
    @st.fragment
    def fetch_live_data_fragment():
        if st.button("Fetch Latest Live Data", use_container_width=True, type="primary"):
            with st.spinner("Scraping live data in background... (You can keep using the dashboard)"):
                try:
                    raw_df = ts.get_live_tracker_data(
                        airtable_base_id=os.environ.get("LAYOFFSFYI_AIRTABLE_BASE"),
                        warn_state_url=os.environ.get("WARN_STATE_URL"),
                    )
                    cleaned_df = cl.clean_tracker_dataframe(raw_df)
                    
                    # Save to CSV so it persists
                    root_dir = Path(__file__).resolve().parent
                    out_dir = root_dir / "data" / "cleaned"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    cleaned_df.to_csv(out_dir / "tracker_cleaned.csv", index=False)
                    
                    st.success("Successfully fetched live data!")
                    st.cache_data.clear() # clear cache to reload
                    st.rerun() # Refresh the whole app to show new data
                except Exception as e:
                    st.error(f"Live scrape failed: {e}")
                    
    fetch_live_data_fragment()

    st.markdown("---")
    st.header("Live News Feed")
    
    @st.cache_data(ttl=3600)
    def fetch_news():
        all_news = []
        for src, url in ns.RSS_FEEDS.items():
            try:
                df_news = ns.fetch_rss_layoff_headlines(url, src)
                if not df_news.empty:
                    all_news.append(df_news)
            except Exception:
                pass
        if all_news:
            return pd.concat(all_news, ignore_index=True)
        return pd.DataFrame()

    with st.spinner("Fetching news..."):
        news_df = fetch_news()
        if not news_df.empty:
            for _, row in news_df.head(5).iterrows():
                st.markdown(f"**[{row['title']}]({row['link']})**")
                st.caption(f"{row['source']} • {row['published']}")
        else:
            st.info("No major layoff headlines found today.")

# ---------------------------------------------------------------------
# Main Data Loading
# ---------------------------------------------------------------------
st.title("Layoff Pulse 2026 — Live Dashboard")

@st.cache_data(ttl=3600)
def load_data():
    csv_path = Path(__file__).resolve().parent / "data" / "cleaned" / "tracker_cleaned.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

if df is None or df.empty:
    st.warning("No local data found. Please click 'Fetch Latest Live Data' in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------
# Dynamic Filtering
# ---------------------------------------------------------------------
st.markdown("### Filter Dashboard")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sectors = ["All"] + sorted(df["sector"].astype(str).unique().tolist())
    selected_sector = st.selectbox("Filter by Sector", sectors)
with col_f2:
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input("Date Range", [min_date, max_date])

# Apply filters
filtered_df = df.copy()
if selected_sector != "All":
    filtered_df = filtered_df[filtered_df["sector"] == selected_sector]
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df["date"].dt.date >= date_range[0]) & (filtered_df["date"].dt.date <= date_range[1])]

if filtered_df.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

# ---------------------------------------------------------------------
# Top Level Metrics
# ---------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Reported Layoffs (rows)", len(filtered_df))
m2.metric("People Affected (sum)", f"{int(filtered_df['laid_off'].sum()):,}")
m3.metric("Distinct Companies", filtered_df['company'].nunique())
m4.metric("Imputed Rows", f"{int(filtered_df['_headcount_imputed'].sum())}")

st.markdown("---")

# ---------------------------------------------------------------------
# Tabs for Advanced Visualizations
# ---------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Trends & Averages", "Sector & Hierarchy", "AI Forecast", "Raw Data Explorer"])

with tab1:
    st.subheader("Rolling Moving Average (30-day)")
    st.plotly_chart(eda.plot_moving_average(filtered_df, window_days=30), use_container_width=True)
    
    st.subheader("Monthly Layoffs Trend")
    st.plotly_chart(eda.plot_monthly_trend(filtered_df), use_container_width=True)

with tab2:
    st.subheader("Layoffs by Sector (vs. Companies Tracked)")
    st.plotly_chart(eda.plot_by_sector(filtered_df), use_container_width=True)
    
    st.subheader("Company Hierarchy (Treemap)")
    st.plotly_chart(eda.plot_treemap(filtered_df), use_container_width=True)

    st.subheader("Data Integrity: Reported vs Imputed")
    st.plotly_chart(eda.plot_imputation_breakdown(filtered_df), use_container_width=True)

with tab3:
    st.subheader("Forecasting (ARIMA vs Baseline)")
    st.markdown("Select a sector to generate a 3-6 month AI forecast of expected layoffs based on historical trends.")
    
    fc_col1, fc_col2 = st.columns(2)
    with fc_col1:
        fc_sector = st.selectbox("Forecast Sector", sectors[1:]) # Skip 'All'
    with fc_col2:
        horizon = st.slider("Forecast horizon (months)", 1, 6, 3)

    try:
        series = fc.prepare_monthly_series(df, fc_sector)
        naive_fc = fc.naive_baseline_forecast(series, horizon=horizon)
        
        try:
            arima_fc = fc.arima_forecast(series, horizon=horizon)
        except ValueError as e:
            st.warning(f"ARIMA skipped (not enough data points): {e}")
            arima_fc = naive_fc.copy()
            arima_fc["model"] = "ARIMA_unavailable_fallback_to_naive"

        st.plotly_chart(fc.plot_forecast_comparison(series, naive_fc, arima_fc, fc_sector), use_container_width=True)
        
        with st.expander("Show Confidence Audit"):
            audit = fc.confidence_audit(series, fc_sector)
            for a in audit["assumptions"]:
                st.write(f"**[{a['risk_level']}]** {a['assumption']}  \n*shaky if: {a['shaky_if']}*")
    except Exception as e:
        st.error(f"Could not generate forecast for {fc_sector}: {e}")

with tab4:
    st.subheader("Explore the Cleaned Dataset")
    st.dataframe(
        filtered_df.sort_values(by="date", ascending=False),
        use_container_width=True,
        hide_index=True
    )
