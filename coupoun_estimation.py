import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

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
    df["Date"] = pd.to_datetime(df["year"].astype(str) + "-" +
                                df["Month_num"].astype(str) + "-01", errors="coerce")
    return df.dropna(subset=["Date"])


# ============================================================
# FIX FREQUENCY
# ============================================================

def fix_frequency(freqstr):
    if freqstr is None:
        return "M"
    freqstr = str(freqstr).upper()
    if freqstr.startswith("ME") or freqstr.startswith("M"):
        return "M"
    if freqstr.startswith("QE") or freqstr.startswith("Q"):
        return "Q"
    return "M"


# ============================================================
# AWARD BUDGETS
# ============================================================

AWARD_BUDGET = {"spot": 2500, "team": 1000, "champion": 5000}

def get_award_type(award_name):
    nm = award_name.lower()
    return "spot" in nm, "team" in nm, "champion" in nm


# ============================================================
# HOLT-WINTERS FORECAST
# ============================================================

def _holt_winters_forecast(series, periods, seasonal_period):

    # no data
    if series is None or len(series) == 0:
        freq = "M" if seasonal_period == 12 else "Q"
        idx = pd.date_range(pd.Timestamp.today(), periods=periods + 1, freq=freq)
        return pd.Series([0] * (periods + 1), index=idx)

    # not enough points
    if len(series) < 2:
        last = series.index[-1]
        freq = fix_frequency(series.index.freqstr or ("M" if seasonal_period == 12 else "Q"))
        idx = pd.date_range(last, periods=periods + 1, freq=freq)
        return pd.Series([series.iloc[-1]] * (periods + 1), index=idx)

    if series.index.freq is None:
        series = series.asfreq("M" if seasonal_period == 12 else "Q")

    def fallback():
        last = series.index[-1]
        freq = fix_frequency(series.index.freqstr)
        next_period = pd.date_range(last, periods=2, freq=freq)[1]
        idx = pd.date_range(next_period, periods=periods, freq=freq)
        fc = pd.Series([series.mean()] * periods, index=idx)
        return pd.concat(
            [pd.Series([series.iloc[-1]], index=[series.index[-1]]), fc]
        )

    configs = [
        {"trend": "add", "seasonal": "add", "seasonal_periods": seasonal_period},
        {"trend": "add", "seasonal": "mul", "seasonal_periods": seasonal_period},
        {"trend": None, "seasonal": "add", "seasonal_periods": seasonal_period},
        {"trend": None, "seasonal": None, "seasonal_periods": None},
    ]

    for cfg in configs:
        try:
            if cfg["seasonal"] is None:
                model = ExponentialSmoothing(series, trend=cfg["trend"])
            else:
                model = ExponentialSmoothing(
                    series,
                    trend=cfg["trend"],
                    seasonal=cfg["seasonal"],
                    seasonal_periods=cfg["seasonal_periods"],
                )
            fit = model.fit(optimized=True, remove_bias=False)
            raw_fc = fit.forecast(periods)

            last = series.index[-1]
            freq = fix_frequency(series.index.freqstr)
            next_period = pd.date_range(last, periods=2, freq=freq)[1]
            idx = pd.date_range(next_period, periods=periods, freq=freq)
            raw_fc.index = idx

            return pd.concat(
                [pd.Series([series.iloc[-1]], index=[series.index[-1]]), raw_fc]
            )

        except:
            continue

    return fallback()

@st.cache_data(show_spinner=False)
def holtwinters_auto_forecast(series, periods, seasonal_period):
    return _holt_winters_forecast(series, periods, seasonal_period)



# ============================================================
# MAIN APP
# ============================================================

def show_coupon_estimation():

    st.title("Coupon Estimation App")

    tab1, tab2 = st.tabs(["Forecasting Dashboard", "Methodology"])

    # ========================================================
    # TAB 1 — FORECASTING
    # ========================================================

    with tab1:

        sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
        df = pd.read_csv(
            f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
        )
        df.columns = df.columns.str.strip()
        df["Coupon Amount"] = safe_numeric(df["Coupon Amount"]).fillna(0)
        df = create_date(df)

        st.subheader("Filters")

        # --------------------------
        # LAST 3 YEARS DEFAULT
        # --------------------------
        years = sorted(df["year"].unique())
        default_years = years[-3:] if len(years) >= 3 else years

        # --------------------------
        # BLOCK unwanted keywords
        # --------------------------
        raw_awards = df["New_Award_title"].dropna().astype(str)

        blocked_keywords = [
            "aswome", "awesome", "asomw", "ossoc", "assoc", "occ", "ota"
        ]

        clean_awards = raw_awards[
            ~raw_awards.str.lower().str.contains("|".join(blocked_keywords))
        ].unique()

        award_list = sorted(clean_awards.tolist())

        # --------------------------
        # DEFAULT = Spot
        # --------------------------
        default_spot = next((a for a in award_list if "spot" in a.lower()), award_list[0])

        col1, col2 = st.columns(2)

        year_filter = col1.multiselect("Select Year(s)", years, default=default_years)
        award_filter = col2.selectbox("Select Award Title", award_list,
                                      index=award_list.index(default_spot))

        # Filter data
        df_f = df[df["year"].isin(year_filter)]
        df_f = df_f[df_f["New_Award_title"] == award_filter]

        has_spot, has_team, has_champion = get_award_type(award_filter)

        # Time series
        monthly = df_f.groupby(pd.Grouper(key="Date", freq="M"))["Coupon Amount"] \
                       .count().asfreq("M").fillna(0)

        quarterly = df_f.groupby(pd.Grouper(key="Date", freq="Q"))["Coupon Amount"] \
                         .count().asfreq("Q").fillna(0)

        # Forecasts
        monthly_fc = holtwinters_auto_forecast(monthly, 6, 12) \
            if (has_spot or has_champion) else None

        quarterly_fc = holtwinters_auto_forecast(quarterly, 4, 4) \
            if has_team else None

        # =====================================================
        # FIXED BUDGET LAYOUT 3 COLUMNS ALWAYS
        # =====================================================
        st.subheader("Required Budget (Next Period Only)")

        col_spot, col_champion, col_team = st.columns(3)

        def next_val(fc):
            try: return fc.iloc[1]
            except: return fc.iloc[-1]

        # -------- SPOT --------
        if has_spot:
            col_spot.metric("Spot - Next Month",
                            f"₹{int(next_val(monthly_fc)*2500):,}")
        else:
            col_spot.metric("Spot - Next Month", "—")

        # -------- CHAMPION --------
        if has_champion:
            col_champion.metric("Champion - Next Quarter",
                                f"₹{int(next_val(monthly_fc)*5000):,}")
        else:
            col_champion.metric("Champion - Next Quarter", "—")

        # -------- TEAM --------
        if has_team:
            col_team.metric("Team - Next Quarter",
                            f"₹{int(next_val(quarterly_fc)*1000):,}")
        else:
            col_team.metric("Team - Next Quarter", "—")

        # =====================================================
        # FIXED: SHOW CHAMPION GRAPH + GREEN THICK FORECAST LINE
        # =====================================================

        if has_spot or has_champion:
            st.subheader("Monthly Forecast – Holt-Winters")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly.index, y=monthly, name="Actual"
            ))

            fig.add_trace(go.Scatter(
                x=monthly_fc.index,
                y=monthly_fc,
                name="Forecast",
                line=dict(color="green", width=4, dash="dash")
            ))

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(monthly_fc.to_frame("Predicted Count"))

        if has_team:
            st.subheader("Quarterly Forecast – Holt-Winters")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=quarterly.index, y=quarterly, name="Actual"
            ))
            fig.add_trace(go.Scatter(
                x=quarterly_fc.index,
                y=quarterly_fc,
                name="Forecast",
                line=dict(color="green", width=4, dash="dash")
            ))

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(quarterly_fc.to_frame("Predicted Count"))

    # ========================================================
    # TAB 2 — METHODOLOGY
    # ========================================================

    with tab2:

        st.header("Forecasting Methodology")

        perf_df = pd.DataFrame({
            "Model": ["Holt-Winters", "ARIMA (2,1,0)",
                      "SARIMA ((2,1,0),(0,0,0,4))", "Moving Average"],
            "MAE": [12.11, 13.60, 14.29, 15.66],
            "RMSE": [18.14, 19.09, 18.69, 21.50],
            "MAPE (%)": [41.32, 49.93, 56.97, 59.47]
        })

        st.subheader("Model Accuracy Comparison")
        st.dataframe(perf_df)

        st.subheader("Model Visualizations")
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)

        c1.image("holt winters.png", caption="Holt-Winters Forecast", use_column_width=True)
        c2.image("arima.png", caption="ARIMA Model", use_column_width=True)
        c3.image("sarima.png", caption="SARIMA Model", use_column_width=True)
        c4.image("mv.png", caption="Moving Average Model", use_column_width=True)


# Run App
if __name__ == "__main__":
    show_coupon_estimation()