import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------
# Global Glass / KPI CSS
# -------------------------------------------------
GLASS_KPI_CSS = """
<style>
.metric-card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(180, 180, 180, 0.7);
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.10);
  text-align: center;
}
.metric-card h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.25rem;
}
.metric-card h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

/* KPI label + ? helper */
.kpi-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.kpi-help {
  font-size: 0.75rem;
  color: #6b7280;
  border-radius: 999px;
  border: 1px solid #d4d4d8;
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: help;
  background-color: #f9fafb;
}

/* Optional: light glass for all charts */
.stPlotlyChart {
  background: radial-gradient(circle at top left,
                              rgba(255,255,255,0.85),
                              rgba(243,244,246,0.98));
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(209, 213, 219, 0.9);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
}
</style>
"""


def show_recognition_individual_tab():
    """Display individual recognition analysis with filters, KPIs, and insights"""

    # Inject CSS
    st.markdown(GLASS_KPI_CSS, unsafe_allow_html=True)

    # ---------------- LOAD DATA ----------------
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)

    # ---------------- CLEAN DATA ----------------
    df["Team name"] = df["Team name"].fillna("Unknown Team")
    df["Employee Name"] = df["Employee Name"].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Add month if available
    if "month" not in df.columns and "Award Date" in df.columns:
        df["Award Date"] = pd.to_datetime(df["Award Date"], errors="coerce")
        df["month"] = df["Award Date"].dt.month

    st.header("Individual Recognition Analysis")

    # ============================================================
    # FILTER SECTION — HORIZONTAL
    # ============================================================

    st.markdown("### 🔎 Filters")

    # ----------- YEAR FILTER BASE -----------
    all_years = sorted(df["year"].dropna().unique())
    year_options = ["All"] + [str(int(y)) for y in all_years]

    # FILTER ROW (Horizontal UI)
    f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1.2, 0.6])

    # ------------------ YEAR ------------------
    with f1:
        selected_years = st.multiselect(
            "Select Year(s)",
            year_options,
            default=["All"],
            key="ind_years_multiselect",   # unique key
        )

    # Create temporary DF based on earlier filters
    temp_df = df.copy()
    if "All" not in selected_years:
        temp_df = temp_df[temp_df["year"].isin([int(y) for y in selected_years])]

    # ------------------ AWARD TYPE ------------------
    with f2:
        award_options = ["All"] + sorted(temp_df["New_Award_title"].dropna().unique())
        selected_awards = st.multiselect(
            "Select Award Title",
            award_options,
            default=["All"],
            key="ind_awards_multiselect",  # unique key
        )

    if "All" not in selected_awards:
        temp_df = temp_df[temp_df["New_Award_title"].isin(selected_awards)]

    # ------------------ TEAM ------------------
    with f3:
        team_options = ["All"] + sorted(temp_df["Team name"].dropna().unique())
        selected_team = st.selectbox(
            "Select Team",
            team_options,
            key="ind_team_selectbox",       # unique key
        )

    if selected_team != "All":
        temp_df = temp_df[temp_df["Team name"] == selected_team]

    # ------------------ EMPLOYEE ------------------
    with f4:
        employee_options = ["All"] + sorted(temp_df["Employee Name"].dropna().unique())
        selected_employee = st.selectbox(
            "Select Employee",
            employee_options,
            key="ind_employee_selectbox",   # unique key
        )

    if selected_employee != "All":
        temp_df = temp_df[temp_df["Employee Name"] == selected_employee]

    # ---------------- CLEAR BUTTON ----------------
    with f5:
        st.write("")
        st.write("")
        if st.button("Clear Filters", key="ind_clear_filters_btn"):
            st.rerun()

    # Final filtered data
    filtered_df = temp_df.copy()

    st.markdown("---")

    # ============================================================
    # KPI SECTION  (GLASS + ? HOVER)
    # ============================================================

    st.markdown("### 📊 Key Performance Indicators Based Upon Filters")

    total_employees = filtered_df["Employee Name"].nunique()
    total_awards = len(filtered_df)

    employee_awards = filtered_df.groupby("Employee Name")["New_Award_title"].count()
    top_performer_awards = employee_awards.max() if len(employee_awards) else 0

    employees_with_multiple = (employee_awards > 1).sum()
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees else 0

    k1, k2, k4, k5 = st.columns(4)

    with k1:
        st.markdown(
            f"""
            <div class="metric-card">
              <h4>
                <span class="kpi-label">
                  Total Employees
                  <span class="kpi-help" title="Number of unique individuals who appear in the filtered dataset.">?</span>
                </span>
              </h4>
              <h2>{total_employees:,}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="metric-card">
              <h4>
                <span class="kpi-label">
                  Total Awards
                  <span class="kpi-help" title="Total count of recognition instances in the filtered data (all award titles combined).">?</span>
                </span>
              </h4>
              <h2>{total_awards:,}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        st.markdown(
            f"""
            <div class="metric-card">
              <h4>
                <span class="kpi-label">
                  Most Awards (Single Individual)
                  <span class="kpi-help" title="Highest number of awards received by any one individual within the current filters.">?</span>
                </span>
              </h4>
              <h2>{top_performer_awards}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k5:
        st.markdown(
            f"""
            <div class="metric-card">
              <h4>
                <span class="kpi-label">
                  Multi-Award Rate
                  <span class="kpi-help" title="Percentage of employees who have received more than one award (repeat recognition).">?</span>
                </span>
              </h4>
              <h2>{recognition_rate:.1f}%</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ============================================================
    # CHART 1: Top Performers SUNBURST
    # ============================================================

    st.subheader("🌟 Most Awards Received For Individuals")

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
        )
        fig1.update_layout(height=600)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

    st.markdown("---")

    # ============================================================
    # CHART 3: Histogram
    # ============================================================

    st.subheader("📌 Recognition Distribution Histogram")

    award_counts_df = employee_awards.reset_index(name="Awards Count")

    fig3 = px.histogram(
        award_counts_df,
        x="Awards Count",
        nbins=20,
        title="Employee Award Count Distribution"
    )
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # CHART 4: Treemap
    # ============================================================

    st.subheader("🎯 Award Types by Top Performers (Treemap)")

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
        )
        fig4.update_layout(height=600)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No award data available.")

    st.markdown("---")

    # ============================================================
    # TABLE 1: Top 20 Recipients
    # ============================================================

    st.subheader("🏆 Top 20 Recipients - Detailed View")

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

    st.markdown("---")

    # ============================================================
    # GAP ANALYSIS
    # ============================================================

    st.subheader("⚠ Recognition Gap Analysis")

    summary = (
        filtered_df.groupby("Employee Name")
        .agg({"New_Award_title": "count", "Team name": "first"}).reset_index()
    )
    summary.columns = ["Employee Name", "Awards", "Team"]

    low_rec = summary[summary["Awards"] <= 2].sort_values("Awards").head(20)

    if len(low_rec):
        st.dataframe(
            low_rec.style.background_gradient(subset=["Awards"], cmap="RdYlGn"),
            use_container_width=True,
            height=400,
        )
        st.info(f"{len(low_rec)} employees have low recognition (≤ 2 awards).")
    else:
        st.success("All employees received 3+ awards!")

    # ============================================================
    # TEAM GAP ANALYSIS
    # ============================================================

    st.subheader("📉 Team-Level Recognition Gaps")

    team_awards = df.groupby("Team name")["New_Award_title"].count().reset_index()
    team_size = df.groupby("Team name")["Employee Name"].nunique().reset_index()

    team_gap = pd.merge(team_awards, team_size, on="Team name")
    team_gap.columns = ["Team", "Total Awards", "Total Employees"]

    team_gap["Awards per Employee"] = (
        team_gap["Total Awards"] / team_gap["Total Employees"]
        if (team_gap["Total Employees"] != 0).all() else 0
    )

    overall_avg = team_gap["Awards per Employee"].mean()

    team_gap["Gap Flag"] = team_gap["Awards per Employee"].apply(
        lambda x: "Low" if x < overall_avg * 0.5
        else ("Moderate" if x < overall_avg else "Good")
    )

    st.dataframe(
        team_gap.style.background_gradient(subset=["Awards per Employee"], cmap="YlOrRd"),
        use_container_width=True
    )

    # ============================================================
    # EMPLOYEES WITH ZERO AWARDS
    # ============================================================

    st.subheader("🚫 Employees With Zero Awards")

    all_employees = df["Employee Name"].unique()
    awarded_employees = df["Employee Name"].unique()  # currently same; zero list will be empty

    zero_awards = list(set(all_employees) - set(awarded_employees))

    zero_awards_df = pd.DataFrame({"Employee Name": zero_awards})

    if len(zero_awards_df):
        zero_awards_df["Team"] = zero_awards_df["Employee Name"].apply(
            lambda x: df[df["Employee Name"] == x]["Team name"].iloc[0]
        )
        st.dataframe(zero_awards_df, use_container_width=True)
        st.warning(f"{len(zero_awards_df)} employees have zero recognition.")
    else:
        st.success("No employees with zero awards!")