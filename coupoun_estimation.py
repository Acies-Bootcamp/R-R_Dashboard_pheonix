import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ============================================================
# CLEANING UTILITIES
# ============================================================

def safe_numeric(s):
    s = s.astype(str).str.replace(",", "", regex=False)
    s = s.str.extract(r"(-?\d+\.?\d*)")[0]
    return pd.to_numeric(s, errors="coerce")


def create_date(df):
    df["Month"] = df["Month"].astype(str).str.strip()

    m1 = pd.to_datetime(df["Month"], format="%B", errors="coerce")
    m2 = pd.to_datetime(df["Month"], format="%b", errors="coerce")
    m3 = pd.to_numeric(df["Month"], errors="coerce")

    df["Month_num"] = m1.dt.month.fillna(m2.dt.month).fillna(m3)
    df = df[df["Month_num"].notna()].copy()
    df["Month_num"] = df["Month_num"].astype(int)

    df["Date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["Month_num"].astype(str) + "-01",
        errors="coerce"
    )
    return df.dropna(subset=["Date"])


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def train_test_split_series(series, test_size=3):
    test_size = min(test_size, max(1, len(series) // 5))
    train = series[:-test_size]
    test = series[-test_size:]
    return train, test


# ============================================================
# MONTHLY FORECAST — HOLT WINTERS
# ============================================================

def holt_winters_monthly(series, periods=6):

    train, test = train_test_split_series(series)

    try:
        model = ExponentialSmoothing(
            train, trend="add", seasonal="add", seasonal_periods=12
        ).fit()
        test_pred = model.forecast(len(test))
    except:
        test_pred = pd.Series([train.mean()] * len(test), index=test.index)

    final_model = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=12
    ).fit()

    forecast = final_model.forecast(periods)

    return forecast, train, test, test_pred


# ============================================================
# QUARTERLY FORECAST — MOVING AVERAGE
# ============================================================

def moving_average_quarterly(series, periods=4):

    train, test = train_test_split_series(series)

    ma_val = train.tail(3).mean()
    test_pred = pd.Series([ma_val] * len(test), index=test.index)

    final_val = series.tail(3).mean()
    idx = pd.date_range(series.index[-1] + series.index.freq, periods=periods, freq="Q")
    forecast = pd.Series([final_val] * periods, index=idx)

    return forecast, train, test, test_pred


# ============================================================
# MAIN STREAMLIT FUNCTION
# ============================================================

def show_coupon_estimation():

    st.title("📦 Coupon Estimation – Holt-Winters (Monthly) + Moving Average (Quarterly)")

    # Load sheet
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    if not {"Month", "year", "Coupon Amount"}.issubset(df.columns):
        st.error("Missing required columns.")
        return

    df["Coupon Amount"] = safe_numeric(df["Coupon Amount"]).fillna(0)
    df = create_date(df)

    # ============================================================
    # FILTERS
    # ============================================================

    st.subheader("🔍 Filters")

    years = sorted(df["year"].unique())
    raw_awards = df["New_Award_title"].dropna().astype(str)

    award_clean = raw_awards[
        ~raw_awards.str.lower().str.contains("asomw") &
        ~raw_awards.str.lower().str.contains("occ")
    ].unique()

    award_list = sorted(award_clean.tolist())

    c1, c2 = st.columns(2)
    year_filter = c1.multiselect("Select Year(s)", years, default=years)
    award_filter = c2.multiselect("Select Award Title(s)", award_list, default=award_list)

    df_filtered = df[df["year"].isin(year_filter)]
    if award_filter:
        df_filtered = df_filtered[df_filtered["New_Award_title"].isin(award_filter)]

    # ============================================================
    # BUILD TIME SERIES
    # ============================================================

    monthly = df_filtered.groupby(pd.Grouper(key="Date", freq="M"))["Coupon Amount"].count().asfreq("M").fillna(0)
    quarterly = df_filtered.groupby(pd.Grouper(key="Date", freq="Q"))["Coupon Amount"].count().asfreq("Q").fillna(0)

    # ============================================================
    # BASIC KPIs
    # ============================================================

    st.subheader("📌 KPIs — Count Based")
    k1, k2 = st.columns(2)
    k1.metric("Total Coupons (Last 12M)", f"{monthly.tail(12).sum():.0f}")
    k2.metric("Avg Monthly Coupons", f"{monthly.tail(12).mean():.0f}")

    # ============================================================
    # FORECAST MODELS
    # ============================================================

    monthly_fc, m_train, m_test, m_test_pred = holt_winters_monthly(monthly, 6)
    quarterly_fc, q_train, q_test, q_test_pred = moving_average_quarterly(quarterly, 4)

    # ============================================================
    # MONTHLY GRAPH
    # ============================================================

    st.subheader("📈 Monthly Forecast – Holt-Winters")

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=m_train.index, y=m_train, name="Train"))
    fig1.add_trace(go.Scatter(x=m_test.index, y=m_test, name="Test"))
    fig1.add_trace(go.Scatter(x=m_test_pred.index, y=m_test_pred, name="Prediction", line=dict(dash="dot"), marker=dict(color="orange")))
    fig1.add_trace(go.Scatter(x=monthly_fc.index, y=monthly_fc, name="Forecast", line=dict(dash="dash"), marker=dict(color="green")))
    st.plotly_chart(fig1, use_container_width=True)

    # ============================================================
    # QUARTERLY GRAPH
    # ============================================================

    st.subheader("📈 Quarterly Forecast – Moving Average")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=q_train.index, y=q_train, name="Train"))
    fig2.add_trace(go.Scatter(x=q_test.index, y=q_test, name="Test"))
    fig2.add_trace(go.Scatter(x=q_test_pred.index, y=q_test_pred, name="Prediction", line=dict(dash="dot"), marker=dict(color="orange")))
    fig2.add_trace(go.Scatter(x=quarterly_fc.index, y=quarterly_fc, name="Forecast", line=dict(dash="dash"), marker=dict(color="green")))
    st.plotly_chart(fig2, use_container_width=True)

    # ============================================================
    # FORECAST TABLES
    # ============================================================

    st.subheader("📄 Monthly Forecast Table")
    st.dataframe(monthly_fc.to_frame("Predicted Count"))

    st.subheader("📄 Quarterly Forecast Table")
    st.dataframe(quarterly_fc.to_frame("Predicted Count"))
