import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_recognition_individual_tab():
    """Display individual recognition analysis with filters, KPIs, and insights"""

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
    # FILTER SECTION — HORIZONTAL LIKE YOUR SCREENSHOT
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
            default=["All"]
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
            default=["All"]
        )

    if "All" not in selected_awards:
        temp_df = temp_df[temp_df["New_Award_title"].isin(selected_awards)]

    # ------------------ TEAM ------------------
    with f3:
        team_options = ["All"] + sorted(temp_df["Team name"].dropna().unique())
        selected_team = st.selectbox(
            "Select Team",
            team_options
        )

    if selected_team != "All":
        temp_df = temp_df[temp_df["Team name"] == selected_team]

    # ------------------ EMPLOYEE ------------------
    with f4:
        employee_options = ["All"] + sorted(temp_df["Employee Name"].dropna().unique())
        selected_employee = st.selectbox(
            "Select Employee",
            employee_options
        )

    if selected_employee != "All":
        temp_df = temp_df[temp_df["Employee Name"] == selected_employee]

    # ---------------- CLEAR BUTTON ----------------
    with f5:
        st.write("")
        st.write("")
        if st.button("Clear Filters"):
            st.rerun()

    # Final filtered data
    filtered_df = temp_df.copy()

    st.markdown("---")

    # ============================================================
    # KPI SECTION
    # ============================================================

    st.markdown("### 📊 Key Performance Indicators Based Upon Filters")

    total_employees = filtered_df["Employee Name"].nunique()
    total_awards = len(filtered_df)

    employee_awards = filtered_df.groupby("Employee Name")["New_Award_title"].count()
    top_performer_awards = employee_awards.max() if len(employee_awards) else 0

    employees_with_multiple = (employee_awards > 1).sum()
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees else 0

    k1, k2, k4, k5 = st.columns(4)
    k1.metric("Total Employees", f"{total_employees:,}")
    k2.metric("Total Awards", f"{total_awards:,}")
    k4.metric("Most Awards Received For Individuals", f"{top_performer_awards}")
    k5.metric("Multi-Award Rate", f"{recognition_rate:.1f}%")

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
    awarded_employees = df["Employee Name"].unique()

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
