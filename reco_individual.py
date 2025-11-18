import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
<<<<<<< HEAD
=======

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

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


# -----------------------
# ✅ GLOSSARY HELPER - COLLAPSIBLE EXPANDER
# -----------------------
def show_glossary(title: str, description: str):
    """Display a collapsible glossary expander below charts"""
    with st.expander(f"📖 {title}", expanded=False):
        st.markdown(description)


def show_recognition_individual_tab():
    """Display individual recognition analysis with filters, KPIs, and insights"""

    st.markdown(GLASS_KPI_CSS, unsafe_allow_html=True)

    # ---------------- LOAD DATA ----------------
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)

    # ---------------- CLEAN DATA ----------------
<<<<<<< HEAD
    # Defensive: ensure expected columns exist; if not, create placeholders to avoid KeyErrors later
=======
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    expected_cols = ["Team name", "Employee Name", "year", "Award Date", "New_Award_title"]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = pd.NA

    df["Team name"] = df["Team name"].fillna("Unknown Team")
    df["Employee Name"] = df["Employee Name"].astype(str).fillna("Unknown")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    if "month" not in df.columns and "Award Date" in df.columns:
        df["Award Date"] = pd.to_datetime(df["Award Date"], errors="coerce")
        df["month"] = df["Award Date"].dt.month

    st.header("Individual Recognition Analysis")

    # ============================================================
    # FILTER SECTION — HORIZONTAL
    # ============================================================

    st.markdown("### 🔎 Filters")

    all_years = sorted(df["year"].dropna().unique())
    year_options = ["All"] + [str(int(y)) for y in all_years]

    f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1.2, 0.6])

    # ------------------ YEAR ------------------
    with f1:
        selected_years = st.multiselect(
            "Select Year(s)",
            year_options,
            default=["All"] if year_options else [],
            key="ind_years_multiselect",
        )

    temp_df = df.copy()
    if selected_years and "All" not in selected_years:
<<<<<<< HEAD
        # convert back to ints safely
=======
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        years_int = []
        for y in selected_years:
            try:
                years_int.append(int(y))
            except Exception:
                pass
        if years_int:
            temp_df = temp_df[temp_df["year"].isin(years_int)]

    # ------------------ AWARD TYPE (OTA REMOVED IN FILTER OPTIONS ONLY) ------------------
    with f2:
        award_titles = temp_df["New_Award_title"].dropna().unique()
<<<<<<< HEAD

        # Remove ANY award containing "ota" (case-insensitive)
=======
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        award_titles = [
            a for a in award_titles
            if "ota" not in str(a).strip().lower()
        ]
<<<<<<< HEAD

=======
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        award_options = ["All"] + sorted(award_titles)

        selected_awards = st.multiselect(
            "Select Award Title",
            award_options,
            default=["All"],
            key="ind_awards_multiselect",
        )

    if selected_awards and "All" not in selected_awards:
        temp_df = temp_df[temp_df["New_Award_title"].isin(selected_awards)]

    # ------------------ TEAM ------------------
    with f3:
        team_options = ["All"] + sorted(temp_df["Team name"].dropna().unique())
        selected_team = st.selectbox(
            "Select Team",
            team_options,
            key="ind_team_selectbox",
        )

    if selected_team and selected_team != "All":
        temp_df = temp_df[temp_df["Team name"] == selected_team]

    # ------------------ EMPLOYEE ------------------
    with f4:
        employee_options = ["All"] + sorted(temp_df["Employee Name"].dropna().unique())
        selected_employee = st.selectbox(
            "Select Employee",
            employee_options,
            key="ind_employee_selectbox",
        )

    if selected_employee and selected_employee != "All":
        temp_df = temp_df[temp_df["Employee Name"] == selected_employee]

    # ---------------- CLEAR BUTTON ----------------
    with f5:
        st.write("")
        st.write("")
        if st.button("Clear Filters", key="ind_clear_filters_btn"):
            st.rerun()

    filtered_df = temp_df.copy()

    st.markdown("---")

    # ============================================================
    # KPI SECTION
    # ============================================================

    st.markdown("### 📊 Key Performance Indicators Based Upon Filters")

<<<<<<< HEAD
    # ----------------------------------------------------------
    # 🔥 UPDATED: Exclude OTA Awards only for KPI calculations
    # ----------------------------------------------------------
    kpi_df = filtered_df[
        ~filtered_df["New_Award_title"].astype(str).str.contains("ota", case=False, na=False)
    ]   # <-- Only KPI uses this
    # ----------------------------------------------------------

    total_employees = kpi_df["Employee Name"].nunique()

    # 🔥 UPDATED: total awards from kpi_df (OTA excluded)
    total_awards = len(kpi_df)

    # 🔥 UPDATED: employee award counts without OTA
    employee_awards = kpi_df.groupby("Employee Name")["New_Award_title"].count()

    top_performer_awards = int(employee_awards.max()) if len(employee_awards) else 0
    employees_with_multiple = int((employee_awards > 1).sum())
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees else 0.0

=======
    kpi_df = filtered_df[
        ~filtered_df["New_Award_title"].astype(str).str.contains("ota", case=False, na=False)
    ]

    total_employees = kpi_df["Employee Name"].nunique()
    total_awards = len(kpi_df)
    employee_awards = kpi_df.groupby("Employee Name")["New_Award_title"].count()

    top_performer_awards = int(employee_awards.max()) if len(employee_awards) else 0
    employees_with_multiple = int((employee_awards > 1).sum())
    recognition_rate = (employees_with_multiple / total_employees * 100) if total_employees else 0.0

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    # KPI Layout
    k1, k2, k4, k5 = st.columns(4)

    with k1:
        st.markdown(
            f"""
            <div class="metric-card">
              <h4><span class="kpi-label">Total Employees
              <span class="kpi-help" title="Unique individuals in filtered data.">?</span></span></h4>
              <h2>{total_employees:,}</h2>
            </div>
            """, unsafe_allow_html=True)

    with k2:
        st.markdown(
            f"""
            <div class="metric-card"><h4>
            <span class="kpi-label">Total Awards
            <span class="kpi-help" title="OTA Awards are excluded only here.">?</span></span></h4>
            <h2>{total_awards:,}</h2></div>
            """, unsafe_allow_html=True)

    with k4:
        st.markdown(
            f"""
            <div class="metric-card"><h4>
<<<<<<< HEAD
            <span class="kpi-label">Individual With the Highest Number of Awards
            <span class="kpi-help" title="Highest award count.">?</span></span></h4>
=======
            <span class="kpi-label">Highest Number of Awards for an Individual<span class="kpi-help" title="Highest award count.">?</span></span></h4>
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
            <h2>{top_performer_awards}</h2></div>
            """, unsafe_allow_html=True)

    with k5:
        st.markdown(
            f"""
            <div class="metric-card"><h4>
            <span class="kpi-label">Multi-Award Rate
            <span class="kpi-help" title="% employees with more than 1 award.">?</span></span></h4>
            <h2>{recognition_rate:.1f}%</h2></div>
            """, unsafe_allow_html=True)
<<<<<<< HEAD
=======

    # ✅ Add KPI Glossary
    show_glossary(
        "Key Performance Indicators",
        "**Total Employees**: Number of unique individuals in the filtered dataset. "
        "**Total Awards**: Count of all awards (OTA awards excluded from this metric). "
        "**Individual With Highest Awards**: The maximum number of awards received by any single employee. "
        "**Multi-Award Rate**: Percentage of employees who have received more than one award, indicating repeat recognition."
    )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

    st.markdown("---")

    # ============================================================
<<<<<<< HEAD
    # CHARTS + TABLES (UNCHANGED — STILL SHOW OTA AWARDS)
=======
    # CHARTS + TABLES
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
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
        
        # ✅ Add Glossary
        show_glossary(
            "Most Awards Received Sunburst Chart",
            "This interactive sunburst chart visualizes the top 15 employees by total awards received. "
            "The **inner ring** represents teams, and the **outer ring** shows individual employees within each team. "
            "The **size and color intensity** of each segment correspond to the number of awards received. "
            "Hover over segments to see detailed breakdown. This helps identify star performers across different teams."
        )
    else:
        st.info("No data available for selected filters.")

    st.markdown("---")

    st.subheader("📌 Recognition Distribution Histogram")
<<<<<<< HEAD
    # award_counts_df uses KPI employee_awards (OTA excluded) — if empty, show message
=======
    
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    if len(employee_awards):
        award_counts_df = employee_awards.reset_index(name="Awards Count")
        fig3 = px.histogram(award_counts_df, x="Awards Count", nbins=20)
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
<<<<<<< HEAD
=======
        
        # ✅ Add Glossary
        show_glossary(
            "Recognition Distribution Histogram",
            "This histogram shows the **distribution of award counts** across all employees. "
            "The **x-axis** represents the number of awards received, and the **y-axis** shows the number of employees in each bracket. "
            "This helps identify if recognition is evenly distributed or if there are outliers with significantly more awards. "
            "A right-skewed distribution indicates most employees have few awards, while a few have many."
        )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    else:
        st.info("No (non-OTA) award counts available for histogram.")

    st.markdown("---")

    st.subheader("🎯 Award Types by Top Performers (Treemap)")

    if len(employee_awards):
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
<<<<<<< HEAD
=======
            
            # ✅ Add Glossary
            show_glossary(
                "Award Types by Top Performers Treemap",
                "This treemap visualizes the **breakdown of award types** for the top 10 performers. "
                "The **first level** shows employee names, and the **second level** shows the types of awards they received. "
                "The **size of each block** represents the count of that award type, and **darker blue colors** indicate higher counts. "
                "This helps understand which types of awards (Team, Spot, Champion, Awesome) are most commonly given to top performers."
            )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        else:
            st.info("No award data available for top performers.")
    else:
        st.info("Not enough data to compute top performers treemap.")

    st.markdown("---")

    st.subheader("🏆 Top 20 Recipients - Detailed View")

    if len(filtered_df):
        top20 = (
            filtered_df.groupby(["Employee Name", "Team name"])
            .agg({"New_Award_title": ["count", lambda x: ", ".join(x.dropna().unique()[:3])]})
            .reset_index()
        )
        top20.columns = ["Employee Name", "Team", "Total Awards", "Award Types (Sample)"]
        top20 = top20.sort_values("Total Awards", ascending=False).head(20)

        st.dataframe(
            top20.style.background_gradient(subset=["Total Awards"], cmap="YlOrRd"),
            use_container_width=True,
            height=400
        )
<<<<<<< HEAD
=======
        
        # ✅ Add Glossary
        show_glossary(
            "Top 20 Recipients Detailed Table",
            "This table lists the **top 20 employees** by total award count, along with their team and a sample of award types received. "
            "The **color gradient** (yellow to red) highlights employees with higher award counts. "
            "**Award Types (Sample)** shows up to 3 unique award types the employee has received. "
            "Use this table to identify consistently high-performing individuals and their recognition patterns."
        )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    else:
        st.info("No award records to show top recipients.")

    st.markdown("---")

    st.subheader("⚠ Recognition Gap Analysis")

    if len(filtered_df):
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
<<<<<<< HEAD
=======
            
            # ✅ Add Glossary
            show_glossary(
                "Recognition Gap Analysis",
                "This table identifies employees with **low recognition levels** (2 or fewer awards). "
                "The **color gradient** (red to green) helps visualize recognition levels, with red indicating very low counts. "
                "Use this analysis to identify potential gaps in your recognition program and ensure all team members are appropriately acknowledged. "
                "Consider whether these employees deserve more recognition or if there are barriers preventing their nominations."
            )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        else:
            st.success("All employees received 3+ awards!")
    else:
        st.info("No filtered employee award data to analyze gaps.")
<<<<<<< HEAD
=======

    st.markdown("---")
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

    st.subheader("📉 Team-Level Recognition Gaps")

    # compute team awards and team sizes from the full df (not filtered_df) — that is consistent with your original code
    team_awards = df.groupby("Team name")["New_Award_title"].count().reset_index()
    team_size = df.groupby("Team name")["Employee Name"].nunique().reset_index()

    team_gap = pd.merge(team_awards, team_size, on="Team name", how="outer")
    team_gap.columns = ["Team", "Total Awards", "Total Employees"]

<<<<<<< HEAD
    # Ensure numeric, replace zeros where appropriate and avoid dividing by zero
    team_gap["Total Awards"] = pd.to_numeric(team_gap["Total Awards"].fillna(0), errors="coerce").fillna(0)
    team_gap["Total Employees"] = pd.to_numeric(team_gap["Total Employees"].fillna(0), errors="coerce").fillna(0)

    # Vectorized safe division: when employees == 0, result will be np.nan -> fill with 0
=======
    team_gap["Total Awards"] = pd.to_numeric(team_gap["Total Awards"].fillna(0), errors="coerce").fillna(0)
    team_gap["Total Employees"] = pd.to_numeric(team_gap["Total Employees"].fillna(0), errors="coerce").fillna(0)

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    team_gap["Awards per Employee"] = team_gap["Total Awards"] / team_gap["Total Employees"].replace({0: np.nan})
    team_gap["Awards per Employee"] = team_gap["Awards per Employee"].fillna(0.0)

    overall_avg = team_gap["Awards per Employee"].mean() if len(team_gap) else 0.0

    team_gap["Gap Flag"] = team_gap["Awards per Employee"].apply(
        lambda x: "Low" if x < overall_avg * 0.5
        else ("Moderate" if x < overall_avg else "Good")
    )

<<<<<<< HEAD
    # ---------------- SAFE SLIDER: filter teams by Awards per Employee --------------
    # Streamlit slider requires min < max. We'll compute min/max and guard if equal.
    min_val = float(team_gap["Awards per Employee"].min()) if len(team_gap) else 0.0
    max_val = float(team_gap["Awards per Employee"].max()) if len(team_gap) else 1.0

    # If all values equal (min == max), bump max slightly so slider works
    if np.isclose(min_val, max_val):
        max_val = min_val + max(0.01, abs(min_val) * 0.01)

    # Offer the slider (float) with small step
=======
    min_val = float(team_gap["Awards per Employee"].min()) if len(team_gap) else 0.0
    max_val = float(team_gap["Awards per Employee"].max()) if len(team_gap) else 1.0

    if np.isclose(min_val, max_val):
        max_val = min_val + max(0.01, abs(min_val) * 0.01)

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    threshold = st.slider(
        "Minimum Awards per Employee to display teams",
        min_value=min_val,
        max_value=max_val,
        value=min_val,
        step=(max_val - min_val) / 100 if (max_val - min_val) > 0 else 0.01,
        format="%.2f",
        key="team_threshold_slider"
<<<<<<< HEAD
    )

    display_team_gap = team_gap[team_gap["Awards per Employee"] >= threshold].sort_values(
        "Awards per Employee", ascending=False
    )

    st.dataframe(
        display_team_gap.style.background_gradient(subset=["Awards per Employee"], cmap="YlOrRd"),
        use_container_width=True
    )

    st.markdown("---")
=======
    )

    display_team_gap = team_gap[team_gap["Awards per Employee"] >= threshold].sort_values(
        "Awards per Employee", ascending=False
    )
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

    st.dataframe(
        display_team_gap.style.background_gradient(subset=["Awards per Employee"], cmap="YlOrRd"),
        use_container_width=True
    )
    
    # ✅ Add Glossary
    show_glossary(
        "Team-Level Recognition Gaps",
        "This table analyzes **awards per employee** at the team level to identify potential recognition gaps. "
        "**Awards per Employee** is calculated by dividing total team awards by the number of team members. "
        "**Gap Flag** categorizes teams as 'Low' (below 50% of average), 'Moderate' (below average), or 'Good' (above average). "
        "Use the **slider above** to filter teams by minimum awards per employee threshold. "
        "Teams with low ratios may need attention to ensure equitable recognition across the organization."
    )

<<<<<<< HEAD
    # The original code attempted to find zero-award employees by comparing all_employees vs awarded_employees
    # but both were sourced from the same df with awards, so that results in an empty set.
    # We'll only compute zero-awards if the sheet provides a full employee roster (column name 'All Employees' or 'Employee Roster')
    roster_col_candidates = [c for c in df.columns if c.lower() in ("all employees", "employee roster", "employee_list", "roster")]
    if roster_col_candidates:
        roster_col = roster_col_candidates[0]
        all_employees = pd.Series(df[roster_col].dropna().unique()).astype(str)
        awarded_employees = pd.Series(df[df["New_Award_title"].notna()]["Employee Name"].unique()).astype(str)
        zero_awards = list(set(all_employees) - set(awarded_employees))
        zero_awards_df = pd.DataFrame({"Employee Name": sorted(zero_awards)})
    else:
        # No roster available in the loaded sheet — inform user and skip
        zero_awards_df = pd.DataFrame()
        st.info("No full employee roster found in the sheet — cannot compute employees with zero awards. "
                "If you have a roster column, name it 'All Employees' or 'Employee Roster'.")

    if len(zero_awards_df):
        # try to find team where possible
        def find_team_for_emp(emp):
            subset = df[df["Employee Name"].astype(str) == str(emp)]
            if len(subset) and subset["Team name"].notna().any():
                return subset["Team name"].iloc[0]
            return "Unknown Team"

        zero_awards_df["Team"] = zero_awards_df["Employee Name"].apply(find_team_for_emp)
        st.dataframe(zero_awards_df, use_container_width=True)
        st.warning(f"{len(zero_awards_df)} employees have zero recognition.")
    else:
        if roster_col_candidates:
            st.success("No employees with zero awards (based on provided roster).")
        else:
            # Already displayed info() above explaining absence of roster
            pass
=======
    st.markdown("---")


if __name__ == "__main__":
    show_recognition_individual_tab()
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
