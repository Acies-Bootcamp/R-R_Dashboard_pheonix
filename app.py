import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="R&R Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
SHEET_KEY = "1ocBuWqHA4e9m2-qyEMvfWqed6SUOEHlj_c2GenObysc"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_KEY}/export?format=csv"


@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(CSV_URL)

    df.columns = [c.strip() for c in df.columns]

    if "year" in df:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")

    if "Month" in df:
        df["Month"] = (
            df["Month"].astype(str)
            .str.strip()
            .str.title()
        )

        mapping = {
            "January": "Jan", "February": "Feb", "March": "Mar",
            "April": "Apr", "May": "May", "June": "Jun",
            "July": "Jul", "August": "Aug", "September": "Sep",
            "October": "Oct", "November": "Nov", "December": "Dec"
        }
        df["Month"] = df["Month"].replace(mapping)

        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul",
                       "Aug","Sep","Oct","Nov","Dec"]

        df["month_num"] = pd.Categorical(df["Month"],
                                         categories=month_order,
                                         ordered=True).codes + 1

    for col in ["Employee Name", "Team name", "New_Award_title", "Nominated By"]:
        if col in df:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    return df


df = load_data()

# --------------------------------------------------
# SIDEBAR FILTERS (Dropdown)
# --------------------------------------------------
st.sidebar.header("🔎 Filters")

years = sorted(df["year"].dropna().unique())
teams = sorted(df["Team name"].unique())
awards = sorted(df["New_Award_title"].unique())
managers = sorted(df["Nominated By"].unique())
months_all = ["All", "Jan","Feb","Mar","Apr","May","Jun","Jul",
              "Aug","Sep","Oct","Nov","Dec"]

sel_year = st.sidebar.selectbox("Year", ["All"] + list(years))
sel_team = st.sidebar.selectbox("Team", ["All"] + teams)
sel_award = st.sidebar.selectbox("Award Title", ["All"] + awards)
sel_manager = st.sidebar.selectbox("Manager", ["All"] + managers)
sel_month = st.sidebar.selectbox("Month", months_all)

# Apply filters
df_f = df.copy()

if sel_year != "All":
    df_f = df_f[df_f["year"] == sel_year]

if sel_team != "All":
    df_f = df_f[df_f["Team name"] == sel_team]

if sel_award != "All":
    df_f = df_f[df_f["New_Award_title"] == sel_award]

if sel_manager != "All":
    df_f = df_f[df_f["Nominated By"] == sel_manager]

if sel_month != "All":
    df_f = df_f[df_f["Month"] == sel_month]

# --------------------------------------------------
# KPI ROW
# --------------------------------------------------
st.title("🏆 R&R Awards Dashboard — Single Page")

c1, c2, c3, c4, c5 = st.columns(5)

total_awards = len(df_f)
unique_employees = df_f["Employee Name"].nunique()
unique_managers = df_f["Nominated By"].nunique()
unique_teams = df_f["Team name"].nunique()
avg_awards = round(total_awards / unique_employees, 2) if unique_employees else 0

c1.metric("Total Awards", total_awards)
c2.metric("Employees Recognized", unique_employees)
c3.metric("Managers Nominating", unique_managers)
c4.metric("Teams", unique_teams)
c5.metric("Avg Awards / Employee", avg_awards)

# --------------------------------------------------
# DOWNLOAD OPTIONS
# --------------------------------------------------
st.subheader("⬇️ Download Data")

col_dl1, col_dl2 = st.columns(2)

with col_dl1:
    st.download_button(
        "Download CSV",
        df_f.to_csv(index=False).encode("utf-8"),
        file_name="filtered_rr.csv",
        mime="text/csv"
    )

with col_dl2:
    def excel_bytes(df):
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="data")
        return bio.getvalue()

    st.download_button(
        "Download Excel",
        excel_bytes(df_f),
        file_name="filtered_rr.xlsx"
    )

st.divider()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 , tab7= st.tabs([
    "📊 Dashboard",
    "🏅 Award Types",
    "👥 Teams",
    "👔 Managers",
    "🧑‍💼 Employees",
    "📅 Trends",
    "📈 Insights",
])

# --------------------------------------------------
# TAB 1 — Dashboard
# --------------------------------------------------
with tab1:
    st.subheader("Top Employees & Teams")

    col1, col2 = st.columns(2)

    # Top Employees
    top_ind = (
        df_f.groupby("Employee Name")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
        .head(15)
    )

    fig = px.bar(
        top_ind,
        x="Total Awards",
        y="Employee Name",
        orientation="h",
        title="Top Employees"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    col1.plotly_chart(fig, use_container_width=True)

    # Top Teams
    top_teams = (
        df_f.groupby("Team name")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
        .head(15)
    )

    fig = px.bar(
        top_teams,
        x="Total Awards",
        y="Team name",
        orientation="h",
        title="Top Teams"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    col2.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TAB 2 — Award Types  (FIXED)
# --------------------------------------------------
with tab2:
    st.subheader("Award Popularity")

    # FIXED block
    award_counts = (
        df_f["New_Award_title"]
        .value_counts()
        .reset_index()
    )
    award_counts.columns = ["Award Title", "Count"]

    fig = px.bar(
        award_counts,
        x="Award Title",
        y="Count",
        title="Awards by Type"
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TAB 3 — Teams
# --------------------------------------------------
with tab3:
    st.subheader("Team Recognition Overview")

    teams_data = (
        df_f.groupby("Team name")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
    )

    fig = px.bar(
        teams_data.sort_values("Total Awards", ascending=False),
        x="Team name",
        y="Total Awards",
        title="Teams by Awards"
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TAB 4 — Managers
# --------------------------------------------------
with tab4:
    st.subheader("Manager Influence")

    mgr_counts = (
        df_f.groupby("Nominated By")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
    )

    fig = px.bar(
        mgr_counts.head(20),
        x="Total Awards",
        y="Nominated By",
        orientation="h",
        title="Top Managers Nominating"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TAB 5 — Employees
# --------------------------------------------------
with tab5:
    st.subheader("Employee Profile")

    emp_list = sorted(df_f["Employee Name"].unique())
    sel_emp = st.selectbox("Choose Employee", emp_list)

    emp_df = df_f[df_f["Employee Name"] == sel_emp]

    c1, c2 = st.columns(2)

    top_title = emp_df["New_Award_title"].value_counts().idxmax()
    c1.metric("Most Received Award", top_title)

    top_mgr = emp_df["Nominated By"].value_counts().idxmax()
    c2.metric("Most Frequent Nominator", top_mgr)

    if "year" in emp_df:
        y = emp_df.groupby("year")["New_Award_title"].count().reset_index(name="Total")
        fig = px.line(y, x="year", y="Total", markers=True, title=f"{sel_emp} - Awards by Year")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# TAB 6 — Trends
# --------------------------------------------------
with tab6:
    st.subheader("Yearly & Monthly Trends")

    if "year" in df_f:
        ydf = df_f.groupby("year")["New_Award_title"].count().reset_index(name="Total")
        fig = px.line(
            ydf,
            x="year",
            y="Total",
            markers=True,
            title="Yearly Trend"
        )
        st.plotly_chart(fig, use_container_width=True)

    if "Month" in df_f:
        mdf = df_f.groupby("Month")["New_Award_title"].count().reset_index(name="Total")
        fig = px.bar(
            mdf,
            x="Month",
            y="Total",
            title="Monthly Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    # --------------------------------------------------
# TAB 7 — Insights (Visual Data-Proven Hypotheses)
# --------------------------------------------------
with tab7:
    st.subheader("📈 Data-Proven Insights")

    # -------------------------------
    # Insight 1: Awards Per Team
    # -------------------------------
    st.markdown("### 🟦 Insight 1: Most & Least Recognized Teams")
    team_awards = (
        df_f.groupby("Team name")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
    )
    fig = px.bar(team_awards, x="Team name", y="Total Awards",
                 title="Team Recognition Comparison",
                 color="Total Awards", color_continuous_scale="Blues")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # Insight 2: Top 10 Individuals' Recognition Share
    # -------------------------------
    st.markdown("### 🟧 Insight 2: Recognition Concentration Among Individuals")
    top10 = (
        df_f.groupby("Employee Name")["New_Award_title"]
        .count()
        .reset_index(name="Awards")
        .sort_values("Awards", ascending=False)
        .head(10)
    )
    total_awards_all = len(df_f)
    concentration_pct = round((top10["Awards"].sum() / total_awards_all) * 100, 2)

    st.metric("Top 10 Individuals Contribution", f"{concentration_pct}%")

    fig = px.bar(top10, x="Awards", y="Employee Name",
                 orientation="h",
                 title="Top 10 Most Recognized Individuals",
                 color="Awards", color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # Insight 3: Award Title Distribution
    # -------------------------------
    st.markdown("### 🟪 Insight 3: Which Award Titles Are Most Used?")
    award_dist = df_f["New_Award_title"].value_counts().reset_index()
    award_dist.columns = ["Award_Title", "Count"]  # FIXED COLUMN NAMES
    fig = px.pie(
    award_dist,
    names="Award_Title",
    values="Count",
    title="Award Title Distribution"
)

    st.plotly_chart(fig, use_container_width=True)  # <-- REQUIRED



    # -------------------------------
    # Insight 4: Manager Influence
    # -------------------------------
    st.markdown("### 🟩 Insight 4: Who Drives Recognition the Most?")
    manager_counts = (
        df_f.groupby("Nominated By")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
    )
    fig = px.bar(manager_counts.head(10),
                 x="Total Awards", y="Nominated By",
                 orientation="h",
                 title="Top Managers by Number of Nominations",
                 color="Total Awards", color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # Insight 5: Year-Month Heatmap (Seasonality)
    # -------------------------------
    st.markdown("### 🟫 Insight 5: Seasonal Recognition Pattern (Heatmap)")
    if "Month" in df_f and "year" in df_f:
        heatmap_data = df_f.pivot_table(index="year", columns="Month",
                                        values="New_Award_title", aggfunc="count", fill_value=0)

        fig = px.imshow(heatmap_data,
                        aspect="auto",
                        color_continuous_scale="Blues",
                        text_auto=True,
                        title="Awards Heatmap (Year × Month)")
        st.plotly_chart(fig, use_container_width=True)

