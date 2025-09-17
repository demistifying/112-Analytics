# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_data, preprocess
from modules.analysis import agg_calls_by_day, agg_calls_by_hour, category_distribution, compute_kpis
import os

st.set_page_config(page_title="112 Helpline Analytics - Sprint 1", layout="wide")

st.title("112 Helpline — Analytics Prototype (Sprint 1)")

# Sidebar: upload or use sample
st.sidebar.header("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload CSV/XLSX (call logs)", type=["csv", "xlsx"])
use_sample = st.sidebar.checkbox("Use sample dummy data", value=True)

# Choose source
df_raw = None
metadata = None
try:
    if uploaded_file is not None:
        df_raw, metadata = load_data(uploaded_file)
        st.sidebar.success(f"Loaded uploaded file ({metadata['record_count']} rows)")
    elif use_sample:
        sample_path = os.path.join("data", "112_calls_synthetic.csv")
        if not os.path.exists(sample_path):
            st.sidebar.error(f"Sample file not found at {sample_path}")
        else:
            df_raw, metadata = load_data(sample_path)
            st.sidebar.info(f"Loaded sample file ({metadata['record_count']} rows)")
    else:
        st.info("Upload a CSV/XLSX file or enable sample dataset from sidebar.")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Preprocess
df = preprocess(df_raw)

# Filters
st.sidebar.header("Filters")
min_date = pd.to_datetime(df["date"]).min()
max_date = pd.to_datetime(df["date"]).max()
date_range = st.sidebar.date_input("Date range", [min_date, max_date])

categories = df["category"].dropna().unique().tolist()
selected_categories = st.sidebar.multiselect("Category", options=categories, default=categories)

jurisdictions = df["jurisdiction"].dropna().unique().tolist()
selected_jurisdictions = st.sidebar.multiselect("Jurisdiction", options=jurisdictions, default=jurisdictions)

# Apply filter mask
mask = (
    (pd.to_datetime(df["date"]) >= pd.to_datetime(date_range[0])) &
    (pd.to_datetime(df["date"]) <= pd.to_datetime(date_range[1])) &
    (df["category"].isin(selected_categories)) &
    (df["jurisdiction"].isin(selected_jurisdictions))
)
df_filtered = df[mask].copy()

# Main layout: KPIs and charts
kpi1, kpi2, kpi3 = st.columns(3)
kpis = compute_kpis(df_filtered)
kpi1.metric("Total calls (filtered)", kpis["total_calls"])
kpi2.metric("Avg calls / day", kpis["avg_per_day"])
kpi3.metric("% with coordinates", f"{kpis['with_coords_pct']}%")

st.markdown("---")
left, right = st.columns([2, 1])

# Time series (left)
with left:
    st.subheader("Time Series — Calls by Day")
    ts_df = agg_calls_by_day(df_filtered, date_col="date")
    if ts_df.empty:
        st.info("No data for selected filters.")
    else:
        fig = px.line(ts_df, x="date", y="count", labels={"date": "Date", "count": "Calls"})
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Hourly Distribution")
    hr = agg_calls_by_hour(df_filtered, hour_col="hour")
    fig2 = px.bar(hr, x="hour", y="count", labels={"hour": "Hour of day", "count": "Calls"})
    st.plotly_chart(fig2, use_container_width=True)

# Category distribution (right)
with right:
    st.subheader("Category Distribution")
    cat_df = category_distribution(df_filtered, category_col="category")
    if not cat_df.empty:
        fig3 = px.pie(cat_df, names="category", values="count", title="Calls by Category")
        st.plotly_chart(fig3, use_container_width=True)
    st.markdown("### Data Sample")
    st.dataframe(df_filtered.head(10))

st.markdown("---")
st.write("Debug: data source metadata")
st.json(metadata)
