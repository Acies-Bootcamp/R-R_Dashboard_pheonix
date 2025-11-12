import streamlit as st
import pandas as pd
import plotly.express as px


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

    st.header("🏅 Individual Recognition Analysis")

    # ============================================================
    # FILTERS SECTION
        # ============================================================
    # FILTERS SECTION
    # ============================================================
    st.markdown("### 🎯 Filters")

    # ---- Prepare dropdown options ----
    years = sorted(df["year"].dropna().unique())
    year_options = ["All"] + [str(int(y)) for y in years]
    award_types = sorted(df["New_Award_title"].dropna().unique())
    award_options = ["All"] + list(award_types)
    teams = sorted(df["Team name"].dropna().unique())
    employees = sorted(df["Employee Name"].dropna().unique())

    # ---- Check if clear flag exists ----
    if "reset_filters" not in st.session_state:
        st.session_state.reset_filters = False

    # ---- When user clicks "Clear Filters" ----
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.4])

    if st.session_state.reset_filters:
        # Set defaults
        default_years = ["All"]
        default_awards = ["All"]
        default_team = "All"
        default_employee = "All"
    else:
        default_years = st.session_state.get("year_filter", ["All"])
        default_awards = st.session_state.get("award_filter", ["All"])
        default_team = st.session_state.get("team_filter", "All")
        default_employee = st.session_state.get("emp_filter", "All")

    # ---- Widgets ----
    with col1:
        selected_years = st.multiselect(
            "📆 Year(s)",
            year_options,
            default=default_years,
            key="year_filter",
        )

    with col2:
        selected_awards = st.multiselect(
            "🏆 Award Type(s)",
            award_options,
            default=default_awards,
            key="award_filter",
        )

    with col3:
        selected_team = st.selectbox(
            "👥 Select Team (optional)",
            ["All"] + teams,
            index=(["All"] + teams).index(default_team)
            if default_team in ["All"] + teams else 0,
            key="team_filter",
        )

    with col4:
        selected_employee = st.selectbox(
            "🧑‍💼 Select Employee (optional)",
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
            st.success("✅ All filters cleared! Showing complete data.")
            st.rerun()

    # Reset clear flag after reload
    if st.session_state.reset_filters:
        st.session_state.reset_filters = False

    # ---------------- APPLY FILTERS ----------------
    filtered_df = df.copy()

    if "All" not in selected_years and len(selected_years) > 0:
        filtered_df = filtered_df[filtered_df["year"].isin([int(y) for y in selected_years])]

    if "All" not in selected_awards and len(selected_awards) > 0:
        filtered_df = filtered_df[filtered_df["New_Award_title"].isin(selected_awards)]

    if selected_team != "All":
        filtered_df = filtered_df[filtered_df["Team name"] == selected_team]

    if selected_employee != "All":
        filtered_df = filtered_df[filtered_df["Employee Name"] == selected_employee]
    # ---------------- APPLY FILTERS ----------------
    filtered_df = df.copy()

    if "All" not in selected_years and len(selected_years) > 0:
        filtered_df = filtered_df[filtered_df["year"].isin([int(y) for y in selected_years])]

    if "All" not in selected_awards and len(selected_awards) > 0:
        filtered_df = filtered_df[filtered_df["New_Award_title"].isin(selected_awards)]

    if selected_team != "All":
        filtered_df = filtered_df[filtered_df["Team name"] == selected_team]

    if selected_employee != "All":
        filtered_df = filtered_df[filtered_df["Employee Name"] == selected_employee]

    st.markdown("---")

    # ============================================================
    # KPI METRICS SECTION
    # ============================================================
    st.markdown("### 📊 Key Performance Indicators")

    total_employees = filtered_df["Employee Name"].nunique()
    total_awards = len(filtered_df)
    avg_awards_per_employee = total_awards / total_employees if total_employees > 0 else 0
    employee_awards = filtered_df.groupby("Employee Name")["New_Award_title"].count()
    top_performer_awards = employee_awards.max() if len(employee_awards) > 0 else 0

    employees_with_multiple = (employee_awards > 1).sum()
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees > 0 else 0

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        st.metric("👤 Total Employees", f"{total_employees:,}")
    with kpi_col2:
        st.metric("🏆 Total Awards", f"{total_awards:,}")
    with kpi_col3:
        st.metric("📈 Avg Awards/Employee", f"{avg_awards_per_employee:.2f}")
    with kpi_col4:
        st.metric("⭐ Top Performer Awards", f"{top_performer_awards}")
    with kpi_col5:
        st.metric("🎯 Multi-Award Rate", f"{recognition_rate:.1f}%")

    st.markdown("---")

    # ============================================================
    # ROW 1: Top & Low Recognition
    # ============================================================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌟 Top Performers")
        top_ind = (
            filtered_df.groupby(["Employee Name", "Team name"])["New_Award_title"]
            .count()
            .reset_index(name="Total Awards")
            .sort_values("Total Awards", ascending=False)
            .head(15)
        )
        if len(top_ind) > 0:
            fig1 = px.bar(
                top_ind,
                x="Total Awards",
                y="Employee Name",
                color="Team name",
                orientation="h",
                title="Top 15 Award Recipients",
            )
            fig1.update_yaxes(autorange="reversed")
            fig1.update_layout(height=500, legend_title="Team")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No data available for selected filters.")

    with col2:
        st.subheader("⚠️ Low Recognition Employees")
        low_ind = (
            filtered_df.groupby("Employee Name")["New_Award_title"]
            .count()
            .reset_index(name="Total Awards")
        )
        low_ind = low_ind[low_ind["Total Awards"] <= 1].head(15)
        if len(low_ind) > 0:
            fig2 = px.bar(
                low_ind,
                x="Total Awards",
                y="Employee Name",
                orientation="h",
                color="Total Awards",
                color_continuous_scale="Purples",
                title="Employees with 1 or Fewer Awards",
            )
            fig2.update_yaxes(autorange="reversed")
            fig2.update_layout(height=500)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No employees with 1 or fewer awards.")

    st.markdown("---")

    # ============================================================
    # ROW 2: Recognition Histogram & Award Types
    # ============================================================
    col6, col7 = st.columns(2)

    with col6:
        st.subheader("📈 Recognition Distribution Histogram")
        award_counts_df = employee_awards.reset_index(name="Awards Count")
        fig3 = px.histogram(
            award_counts_df,
            x="Awards Count",
            nbins=20,
            title="Employee Award Count Distribution",
            labels={"Awards Count": "Number of Awards", "count": "Number of Employees"},
            color_discrete_sequence=["#636EFA"],
        )
        fig3.update_layout(
            height=400,
            bargap=0.1,
            xaxis_title="Number of Awards",
            yaxis_title="Number of Employees",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col7:
        st.subheader("🏅 Award Types by Top Performers")
        top_10_employees = employee_awards.nlargest(10).index
        top_performers_df = filtered_df[filtered_df["Employee Name"].isin(top_10_employees)]
        award_type_counts = (
            top_performers_df.groupby(["Employee Name", "New_Award_title"])
            .size()
            .reset_index(name="Count")
        )
        fig4 = px.bar(
            award_type_counts,
            x="Employee Name",
            y="Count",
            color="New_Award_title",
            title="Award Type Breakdown - Top 10 Performers",
            barmode="stack",
        )
        fig4.update_layout(height=400, xaxis_tickangle=45, legend_title="Award Type")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # ROW 3: Detailed Tables
    # ============================================================
    col10, col11 = st.columns(2)

    with col10:
        st.subheader("📋 Top 20 Recipients - Detailed View")
        top_20_detailed = (
            filtered_df.groupby(["Employee Name", "Team name"])
            .agg({"New_Award_title": ["count", lambda x: ", ".join(x.unique()[:3])]})
            .reset_index()
        )
        top_20_detailed.columns = ["Employee Name", "Team", "Total Awards", "Award Types (Sample)"]
        top_20_detailed = top_20_detailed.sort_values("Total Awards", ascending=False).head(20)
        st.dataframe(
            top_20_detailed.style.background_gradient(subset=["Total Awards"], cmap="YlOrRd"),
            use_container_width=True,
            height=400,
        )

    with col11:
        st.subheader("🔍 Recognition Gap Analysis")
        employee_award_summary = (
            filtered_df.groupby("Employee Name")
            .agg({"New_Award_title": "count", "Team name": "first"})
            .reset_index()
        )
        employee_award_summary.columns = ["Employee Name", "Awards", "Team"]
        low_recognition = employee_award_summary[
            employee_award_summary["Awards"] <= 2
        ].sort_values("Awards").head(20)
        if len(low_recognition) > 0:
            st.dataframe(
                low_recognition.style.background_gradient(subset=["Awards"], cmap="RdYlGn"),
                use_container_width=True,
                height=400,
            )
            st.info(
                f"💡 {len(low_recognition)} employees shown with minimal recognition. "
                "Consider recognizing their contributions!"
            )
        else:
            st.success("✅ All employees in the filtered dataset have received 3+ awards!")

