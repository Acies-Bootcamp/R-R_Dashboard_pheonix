import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_css   # ⭐ Global CSS loader


# ============================================================
# GLASS CARD HELPERS
# ============================================================

def chart_card_start(title):
    st.markdown(
        f"""
        <div class='glass-card' style='padding:20px; margin-top:15px;'>
            <h3 style="margin-bottom:10px;">{title}</h3>
        """,
        unsafe_allow_html=True
    )


def chart_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# MAIN FUNCTION
# ============================================================

def show_recognition_individual_tab():

    # ⭐ Load theme.css first
    load_css()

    # ---------------- LOAD DATA ----------------
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)

    # ---------------- CLEAN DATA ----------------
    df["Team name"] = df["Team name"].fillna("Unknown Team")
    df["Employee Name"] = df["Employee Name"].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    if "month" not in df.columns and "Award Date" in df.columns:
        df["Award Date"] = pd.to_datetime(df["Award Date"], errors="coerce")
        df["month"] = df["Award Date"].dt.month

    st.header("🏅 Individual Recognition Analysis")

    # ============================================================
    # FILTERS SECTION
    # ============================================================

    chart_card_start("🎯 Filters")

    years = sorted(df["year"].dropna().unique())
    year_options = ["All"] + [str(int(y)) for y in years]

    award_types = sorted(df["New_Award_title"].dropna().unique())
    award_options = ["All"] + list(award_types)

    teams = sorted(df["Team name"].dropna().unique())
    employees = sorted(df["Employee Name"].dropna().unique())

    if "reset_filters" not in st.session_state:
        st.session_state.reset_filters = False

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.4])

    if st.session_state.reset_filters:
        default_years = ["All"]
        default_awards = ["All"]
        default_team = "All"
        default_employee = "All"
    else:
        default_years = st.session_state.get("year_filter", ["All"])
        default_awards = st.session_state.get("award_filter", ["All"])
        default_team = st.session_state.get("team_filter", "All")
        default_employee = st.session_state.get("emp_filter", "All")

    with col1:
        selected_years = st.multiselect(
            "📆 Year(s)", year_options, default=default_years, key="year_filter"
        )

    with col2:
        selected_awards = st.multiselect(
            "🏆 Award Type(s)", award_options, default=default_awards, key="award_filter"
        )

    with col3:
        selected_team = st.selectbox(
            "👥 Select Team",
            ["All"] + teams,
            index=(["All"] + teams).index(default_team)
            if default_team in ["All"] + teams else 0,
            key="team_filter",
        )

    with col4:
        selected_employee = st.selectbox(
            "🧑‍💼 Select Employee",
            ["All"] + employees,
            index=(["All"] + employees).index(default_employee)
            if default_employee in ["All"] + employees else 0,
            key="emp_filter",
        )

    with col5:
        if st.button("🔄 Clear Filters"):
            st.session_state.reset_filters = True
            for key in ["year_filter", "award_filter", "team_filter", "emp_filter"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ All filters cleared!")
            st.rerun()

    if st.session_state.reset_filters:
        st.session_state.reset_filters = False

    chart_card_end()

    # ---------------- APPLY FILTERS ----------------
    filtered_df = df.copy()

    if "All" not in selected_years:
        filtered_df = filtered_df[filtered_df["year"].isin([int(y) for y in selected_years])]

    if "All" not in selected_awards:
        filtered_df = filtered_df[filtered_df["New_Award_title"].isin(selected_awards)]

    if selected_team != "All":
        filtered_df = filtered_df[filtered_df["Team name"] == selected_team]

    if selected_employee != "All":
        filtered_df = filtered_df[filtered_df["Employee Name"] == selected_employee]

    # ============================================================
    # KPI METRICS SECTION
    # ============================================================

    chart_card_start("📊 Key Performance Indicators")

    total_employees = filtered_df["Employee Name"].nunique()
    total_awards = len(filtered_df)
    avg_awards_per_employee = total_awards / total_employees if total_employees else 0

    employee_awards = filtered_df.groupby("Employee Name")["New_Award_title"].count()
    top_performer_awards = employee_awards.max() if len(employee_awards) else 0

    employees_with_multiple = (employee_awards > 1).sum()
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("👤 Total Employees", f"{total_employees:,}")
    k2.metric("🏆 Total Awards", f"{total_awards:,}")
    k3.metric("📈 Avg Awards/Employee", f"{avg_awards_per_employee:.2f}")
    k4.metric("⭐ Top Performer Awards", f"{top_performer_awards}")
    k5.metric("🎯 Multi-Award Rate", f"{recognition_rate:.1f}%")

    chart_card_end()

    # ============================================================
    # CHART 1: Top Performers (SUNBURST)
    # ============================================================

    chart_card_start("🌟 Top Performers (Sunburst)")

    top_ind = (
        filtered_df.groupby(["Employee Name", "Team name"])["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
        .sort_values("Total Awards", ascending=False)
        .head(15)
    )

    if len(top_ind):
        fig1 = px.sunburst(
            top_ind,
            path=["Team name", "Employee Name"],
            values="Total Awards",
            color="Total Awards",
            color_continuous_scale="Viridis",
            title="Top 15 Award Recipients"
        )
        fig1.update_layout(height=600)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available.")

    chart_card_end()

    # ============================================================
    # CHART 2: Low Recognition Employees
    # ============================================================

    chart_card_start("⚠️ Low Recognition Employees")

    low_ind = (
        filtered_df.groupby("Employee Name")["New_Award_title"]
        .count()
        .reset_index(name="Total Awards")
    )
    low_ind = low_ind[low_ind["Total Awards"] <= 1].head(20)

    if len(low_ind):
        low_sorted = low_ind.sort_values("Total Awards")

        fig2 = px.bar(
            low_sorted,
            x="Employee Name",
            y="Total Awards",
            color="Employee Name",
            title="Employees With 1 or Fewer Awards",
            text="Total Awards"
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.success("🎉 All employees have 2+ awards!")

    chart_card_end()

    # ============================================================
    # CHART 3: Histogram
    # ============================================================

    chart_card_start("📈 Recognition Distribution Histogram")

    award_counts_df = employee_awards.reset_index(name="Awards Count")

    fig3 = px.histogram(
        award_counts_df,
        x="Awards Count",
        nbins=20,
        title="Employee Award Count Distribution"
    )
    fig3.update_layout(height=400)

    st.plotly_chart(fig3, use_container_width=True)

    chart_card_end()

    # ============================================================
    # CHART 4: Treemap
    # ============================================================

    chart_card_start("🏅 Award Types by Top Performers (Treemap)")

    top_10 = employee_awards.nlargest(10).index
    top_df = filtered_df[filtered_df["Employee Name"].isin(top_10)]

    award_type_counts = (
        top_df.groupby(["Employee Name", "New_Award_title"])
        .size()
        .reset_index(name="Count")
    )

    if len(award_type_counts):
        fig4 = px.treemap(
            award_type_counts,
            path=["Employee Name", "New_Award_title"],
            values="Count",
            color="Count",
            color_continuous_scale="Blues",
            title="Award Type Breakdown (Top 10 Performers)"
        )
        fig4.update_layout(height=600)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No award data available.")

    chart_card_end()

    # ============================================================
    # TABLE 1: Top 20 Recipients
    # ============================================================

    chart_card_start("📋 Top 20 Recipients")

    top20 = (
        filtered_df.groupby(["Employee Name", "Team name"])
        .agg({"New_Award_title": ["count", lambda x: ", ".join(x.unique()[:3])]})
        .reset_index()
    )
    top20.columns = ["Employee Name", "Team", "Total Awards", "Award Types (Sample)"]
    top20 = top20.sort_values("Total Awards", ascending=False).head(20)

    st.dataframe(
        top20.style.background_gradient(subset=["Total Awards"], cmap="YlOrRd"),
        use_container_width=True,
        height=400
    )

    chart_card_end()

    # ============================================================
    # TABLE 2: Gap Analysis
    # ============================================================

    chart_card_start("🔍 Recognition Gap Analysis")

    summary = (
        filtered_df.groupby("Employee Name")
        .agg({"New_Award_title": "count", "Team name": "first"})
        .reset_index()
    )
    summary.columns = ["Employee Name", "Awards", "Team"]

    low_rec = summary[summary["Awards"] <= 2].sort_values("Awards").head(20)

    if len(low_rec):
        st.dataframe(
            low_rec.style.background_gradient(subset=["Awards"], cmap="RdYlGn"),
            use_container_width=True,
            height=400,
        )
        st.info(f"💡 {len(low_rec)} employees have minimal recognition.")
    else:
        st.success("🎉 All employees received 3+ awards!")

    chart_card_end()
