import streamlit as st 
import pandas as pd
import plotly.express as px
import re
import html

# -----------------------
# Global Glass / KPI CSS
# -----------------------
glass_css = """
<style>
/* KPI cards */
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

/* Glass effect for all charts */
.stPlotlyChart {
  background: radial-gradient(circle at top left,
                              rgba(255,255,255,0.8),
                              rgba(243,244,246,0.98));
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(209, 213, 219, 0.9);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
}

/* Slightly darker Streamlit table text */
.dataframe th {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}
</style>
"""

# -----------------------
# Helpers
# -----------------------
def normalize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name

def _find_amount_col(df: pd.DataFrame) -> str | None:
    candidates = [
        "Coupon Amount", "Coupon Amount (₹)", "Coupon amount",
        "Coupon", "Amount", "Budget", "Allocation",
        "Award Amount", "Award_Value", "CouponValue", "Coupon_Value"
    ]
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            return lower_cols[cand.lower()]
    for c in df.columns:
        lc = c.lower()
        if any(k in lc for k in ["coupon", "amount", "allocation", "budget"]):
            return c
    return None

def _to_number(series: pd.Series) -> pd.Series:
    s = series.astype(str)
    s = s.str.replace("\u20b9", "", regex=False)  # ₹
    s = s.str.replace(",", "", regex=False)
    s = s.str.strip()
    extracted = s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce").fillna(0.0)

def load_and_process_data():
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df = pd.read_excel(url)

    # Month / Year -> Date
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].astype(str).str.strip().str.capitalize()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['Month_Num'] = df['Month'].map(month_map)
    df['Date'] = pd.to_datetime(
        dict(year=df['year'], month=df['Month_Num'], day=1),
        errors='coerce'
    )

    # Team name normalisation / mapping
    team_mapping = {
        'greenmath': 'Greenmath',
        'edgecore': 'Edgecore',
        'edgecre': 'Edgecore',
        'pr - greenmath launch': 'PR - Greenmath Launch',
    }
    df['Team name'] = (
        df['Team name']
        .astype(str).str.strip().str.lower()
        .map(lambda t: team_mapping.get(t, t))
        .str.title()
    )

    # Amount parsing
    amt_col = _find_amount_col(df)
    df['Amount'] = _to_number(df[amt_col]) if amt_col else 0.0

    return df

def clean_teamname_df(df, column='Team name'):
    df_cleaned = df.dropna(subset=[column]).copy()
    df_cleaned = df_cleaned[
        ~df_cleaned[column].astype(str).str.strip().str.lower().eq('nan')
    ]
    df_cleaned = df_cleaned[
        df_cleaned[column].astype(str).str.strip() != ''
    ]
    return df_cleaned

# -----------------------
# Trend builder
# -----------------------
def build_award_trend(
    df,
    selected_years,
    time_period,
    team_mode,
    selected_team,
    top_team_count,
    employee_team_map=None,
):
    dfs = []

    # --- Team Award ---
    team_award_df = df[df['New_Award_title'] == 'Team Award'].copy()
    team_award_df = clean_teamname_df(team_award_df, column='Team name')
    teams = sorted(team_award_df['Team name'].dropna().unique())

    if team_mode == "All Teams":
        active_teams = teams
    elif team_mode == "Single Team":
        active_teams = [selected_team] if (selected_team and selected_team != "All Teams") else teams
    elif team_mode == "Most Couponed Teams":
        top_teams = team_award_df['Team name'].value_counts().head(top_team_count).index.tolist()
        active_teams = top_teams
    else:
        active_teams = teams

    filtered_team = team_award_df[
        (team_award_df['year'].isin(selected_years)) &
        (team_award_df['Team name'].isin(active_teams))
    ].copy()
    filtered_team = clean_teamname_df(filtered_team, column='Team name')
    if not filtered_team.empty:
        filtered_team['Award_Type'] = 'Team Award'
        dfs.append(filtered_team)

    # --- Awesome Award mapped to Greenmath/Edgecore ---
    if employee_team_map is not None and not employee_team_map.empty:
        filtered_employees = employee_team_map.copy()
    else:
        gm = df[df['Team name'].str.contains('greenmath', case=False, na=False)]
        ec = df[df['Team name'].str.contains('edgecore', case=False, na=False)]
        filtered_employees = pd.concat([gm, ec], ignore_index=True)
        filtered_employees = filtered_employees[['Employee Name', 'Team name']].drop_duplicates()

    awesome_awards_raw = df[df['New_Award_title'] == 'Awesome Award'].copy()
    mapped = awesome_awards_raw.merge(
        filtered_employees,
        on='Employee Name',
        how='left',
        suffixes=('', '_mapped')
    )
    mapped['Team name'] = mapped['Team name_mapped'].fillna(mapped['Team name'])
    mapped = mapped[
        mapped['Team name'].str.contains('greenmath|edgecore', case=False, na=False) &
        mapped['year'].isin(selected_years)
    ].copy()
    mapped = clean_teamname_df(mapped, column='Team name')
    if not mapped.empty:
        mapped['Award_Type'] = 'Awesome Award'
        dfs.append(mapped)

    if not dfs:
        return None, None

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = clean_teamname_df(combined_df, column='Team name')

    if time_period == "Monthly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        combined_df['Period'] = combined_df['Date'].dt.to_period('Y').dt.to_timestamp()

    combined_df = combined_df.dropna(subset=['Period'])

    trend_df = (
        combined_df
        .groupby(['Period', 'Team name', 'Award_Type'], as_index=False)
        .size()
        .rename(columns={'size': 'Award_Count'})
    )
    return trend_df, combined_df

# -----------------------
# Filter by award type (for KPIs)
# -----------------------
def filter_by_award_type(df, award_type_filter):
    if df is None or df.empty:
        return df

    if award_type_filter in [
        "All Awards (Team + Awesome)",
        "Both Team & Awesome",
        "All"
    ]:
        return df[df['New_Award_title'].isin(['Team Award', 'Awesome Award'])]
    elif award_type_filter == "Team Award only":
        return df[df['New_Award_title'] == 'Team Award']
    elif award_type_filter == "Awesome Award only":
        return df[df['New_Award_title'] == 'Awesome Award']
    else:
        return df[df['New_Award_title'].isin(['Team Award', 'Awesome Award'])]

# -----------------------
# KPIs (boxed style with ? hover)
# -----------------------
def display_team_level_kpis(df_allhands: pd.DataFrame, df_kudos: pd.DataFrame):
    distinct_all = int(clean_teamname_df(df_allhands)['Team name'].nunique()) if df_allhands is not None and not df_allhands.empty else 0
    distinct_kudos = int(clean_teamname_df(df_kudos)['Team name'].nunique()) if df_kudos is not None and not df_kudos.empty else 0

    def avg_teams_per_month(df: pd.DataFrame) -> float:
        if df is None or df.empty or 'Date' not in df.columns:
            return 0.0
        monthly = clean_teamname_df(df).groupby(df['Date'].dt.to_period('M'))['Team name'].nunique()
        if monthly.empty:
            return 0.0
        return float(monthly.mean())

    avg_month_all = avg_teams_per_month(df_allhands)
    avg_month_kudos = avg_teams_per_month(df_kudos)

    team_awards_all = 0
    team_awards_kudos = 0
    if df_allhands is not None and not df_allhands.empty and 'New_Award_title' in df_allhands.columns:
        team_awards_all = int((df_allhands['New_Award_title'] == 'Team Award').sum())
    if df_kudos is not None and not df_kudos.empty and 'New_Award_title' in df_kudos.columns:
        team_awards_kudos = int((df_kudos['New_Award_title'] == 'Team Award').sum())
    approx_team_coupons = team_awards_all + team_awards_kudos

    st.subheader("Team-Level KPIs: All Hands vs Kudos Corner")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Teams Recognised (All Hands)
                    <span class="kpi-help" title="Number of distinct teams that received at least one award in the All Hands (Town Hall) system for the selected period.">?</span>
                  </span>
                </h4>
                <h2>{distinct_all}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Teams Recognised (Kudos Corner)
                    <span class="kpi-help" title="Number of distinct teams that received at least one award via Kudos Corner during the selected period.">?</span>
                  </span>
                </h4>
                <h2>{distinct_kudos}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Avg Teams/Month (All Hands)
                    <span class="kpi-help" title="Average number of unique teams recognised per month in the All Hands system (based on the selected years and filters).">?</span>
                  </span>
                </h4>
                <h2>{avg_month_all:.1f}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Avg Teams/Month (Kudos Corner)
                    <span class="kpi-help" title="Average number of unique teams recognised per month via Kudos Corner in the selected period.">?</span>
                  </span>
                </h4>
                <h2>{avg_month_kudos:.1f}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c5:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Approx Team Award Coupons
                    <span class="kpi-help" title="Total count of Team Award instances across All Hands and Kudos Corner. This is a rough proxy for how many team coupons were distributed.">?</span>
                  </span>
                </h4>
                <h2>{approx_team_coupons}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.caption(
        "Approx Team Award Coupons = count of Team Award instances (All Hands + Kudos Corner). "
        "Kudos Corner currently has only a few months of data, so KPIs are descriptive."
    )

# -----------------------
# Team frequency table
# -----------------------
def build_team_frequency_table(
    df: pd.DataFrame,
    selected_years,
    team_mode,
    selected_team,
    top_team_count,
    freq_award_filter: str,
    employee_team_map=None
):
    df_freq = df[df['year'].isin(selected_years)].copy()

    if employee_team_map is not None and not employee_team_map.empty:
        awesome_award_rows = df_freq[df_freq['New_Award_title'] == 'Awesome Award'].copy()
        mapped = awesome_award_rows.merge(
            employee_team_map, on='Employee Name', how='left', suffixes=('', '_mapped')
        )
        mapped['Team name'] = mapped['Team name_mapped'].fillna(mapped['Team name'])
        mapped = mapped.drop(columns=['Team name_mapped'])
        non_awesome = df_freq[df_freq['New_Award_title'] != 'Awesome Award'].copy()
        df_freq = pd.concat([non_awesome, mapped], ignore_index=True)

    if freq_award_filter == "Team Award only":
        df_freq = df_freq[df_freq['New_Award_title'] == 'Team Award']
    elif freq_award_filter == "Awesome Award only":
        df_freq = df_freq[df_freq['New_Award_title'] == 'Awesome Award']
    else:
        df_freq = df_freq[df_freq['New_Award_title'].isin(['Team Award', 'Awesome Award'])]

    df_freq = clean_teamname_df(df_freq, column='Team name')

    if df_freq.empty:
        return pd.DataFrame(columns=[
            "Team",
            "Team size (No. of people recognised)",
            "No. of times team got awarded",
            "Total Team Awards",
            "Total Awesome Awards",
        ])

    if team_mode == "Single Team":
        if selected_team and selected_team != "All Teams":
            df_freq = df_freq[df_freq['Team name'] == selected_team]
    elif team_mode == "Most Couponed Teams":
        counts = df_freq['Team name'].value_counts()
        top_teams = counts.head(top_team_count).index.tolist()
        df_freq = df_freq[df_freq['Team name'].isin(top_teams)]

    if df_freq.empty:
        return pd.DataFrame(columns=[
            "Team",
            "Team size (No. of people recognised)",
            "No. of times team got awarded",
            "Total Team Awards",
            "Total Awesome Awards",
        ])

    grouped = df_freq.groupby('Team name').agg(
        team_size=('Employee Name', 'nunique'),
        times_awarded=('New_Award_title', 'nunique'),
        total_team_awards=('New_Award_title', lambda s: (s == 'Team Award').sum()),
        total_awesome_awards=('New_Award_title', lambda s: (s == 'Awesome Award').sum()),
    ).reset_index()

    grouped['total_awards_internal'] = grouped['total_team_awards'] + grouped['total_awesome_awards']
    grouped = grouped.sort_values('total_awards_internal', ascending=False)

    grouped = grouped.rename(columns={
        'Team name': 'Team',
        'team_size': 'Team size (No. of people recognised)',
        'times_awarded': 'No. of times team got awarded',
        'total_team_awards': 'Total Team Awards',
        'total_awesome_awards': 'Total Awesome Awards',
    })

    grouped = grouped.drop(columns=['total_awards_internal'])

    return grouped

# -----------------------
# Main UI
# -----------------------
def show_recognition_team_tab():
    # inject glass + kpi CSS
    st.markdown(glass_css, unsafe_allow_html=True)

    df = load_and_process_data()

    st.title("Team-Level Trends")
    st.caption(
        "These charts show *team-level trends* combining **Team Awards** and **Awesome Awards**. "
        "**All Hands** represents the legacy ceremony, and **Kudos Corner** represents the new system."
    )

    employee_team_map = (
        df[df['Team name'].str.contains('greenmath|edgecore', case=False, na=False)]
        [['Employee Name', 'Team name']]
        .dropna()
        .drop_duplicates()
    )

    # -------- Filters --------
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        with col1:
            period_options = ["Monthly", "Quarterly", "Yearly"]
            time_period = st.selectbox("Select Period", period_options, index=0)

        with col2:
            years = sorted(df['year'].dropna().unique())
            year_options = ["All"] + list(years)
            selected_years_raw = st.multiselect(
                "Select Year(s)",
                options=year_options,
                default=["All"],
            )
            if "All" in selected_years_raw or not selected_years_raw:
                selected_years = years
            else:
                selected_years = [
                    y for y in selected_years_raw if isinstance(y, (int, float))
                ]

        with col3:
            team_mode = st.selectbox(
                "Display Teams by",
                ["All Teams", "Most Couponed Teams", "Single Team"],
                index=1
            )

        with col4:
            teams_filtered_by_year = sorted(
                clean_teamname_df(df[df['year'].isin(selected_years)])['Team name'].unique()
            )
            top_team_count = (
                st.slider(
                    "No. of Most Couponed Teams",
                    min_value=5,
                    max_value=min(20, len(teams_filtered_by_year)) if teams_filtered_by_year else 5,
                    value=min(10, len(teams_filtered_by_year)) if teams_filtered_by_year else 5
                ) if team_mode == "Most Couponed Teams" else None
            )

        with col5:
            # Default is All Awards
            freq_award_filter = st.selectbox(
                "Awards for Team Frequency",
                ["All Awards (Team + Awesome)", "Team Award only", "Awesome Award only"],
                index=0
            )

        selected_team = (
            st.selectbox("Select Team", ["All Teams"] + teams_filtered_by_year)
            if team_mode == "Single Team"
            else None
        )

    # -------- Split All Hands vs Kudos --------
    nom_col = next((c for c in ['Nominated', 'Nominated In', 'NominatedIn'] if c in df.columns), None)
    if nom_col:
        nom_series = df[nom_col].astype(str)
        mask_kudos = nom_series.str.contains("kudos", case=False, na=False)
        mask_all = nom_series.str.contains("all", case=False, na=False) & ~mask_kudos
        if not mask_all.any():
            mask_all = ~mask_kudos
        df_allhands = df[mask_all].copy()
        df_kudos = df[mask_kudos].copy()
    else:
        df_allhands = df.copy()
        df_kudos = df[df.apply(lambda row: any("kudos" in str(v).lower() for v in row), axis=1)].copy()

    # -------- Build trends --------
    trend_all, combined_all = build_award_trend(
        df_allhands,
        selected_years,
        time_period,
        team_mode,
        selected_team,
        top_team_count,
        employee_team_map=employee_team_map,
    )
    trend_kudos, combined_kudos = build_award_trend(
        df_kudos,
        selected_years,
        time_period,
        team_mode,
        selected_team,
        top_team_count,
        employee_team_map=employee_team_map,
    )

    if (trend_all is None or trend_all.empty) and (trend_kudos is None or trend_kudos.empty):
        st.warning("No data for selected filters.")
        return

    # -------- KPIs --------
    all_df_for_kpi = filter_by_award_type(
        combined_all if combined_all is not None else pd.DataFrame(columns=df.columns),
        freq_award_filter
    )
    kudos_df_for_kpi = filter_by_award_type(
        combined_kudos if combined_kudos is not None else pd.DataFrame(columns=df.columns),
        freq_award_filter
    )
    display_team_level_kpis(all_df_for_kpi, kudos_df_for_kpi)

    # -------- Team Frequency Section --------
    st.subheader("Team Recognition Frequency (Selected Period)")

    freq_df = build_team_frequency_table(
        df,
        selected_years,
        team_mode,
        selected_team,
        top_team_count if top_team_count is not None else 10,
        freq_award_filter,
        employee_team_map=employee_team_map
    )

    if freq_df.empty:
        st.info("No team recognition data for the selected filters and award type.")
    else:
        freq_chart_df = freq_df.copy()
        freq_chart_df["Total Awards (Team+Awesome)"] = (
            freq_chart_df["Total Team Awards"] + freq_chart_df["Total Awesome Awards"]
        )

        fig_freq = px.bar(
            freq_chart_df.sort_values("Total Awards (Team+Awesome)", ascending=True),
            x="Total Awards (Team+Awesome)",
            y="Team",
            orientation="h",
            text="Total Awards (Team+Awesome)",
            title="Total Awards (Team + Awesome) by Team"
        )
        fig_freq.update_layout(
            xaxis_title="Total Awards (Team + Awesome)",
            yaxis_title="Team",
            template="plotly_white"
        )
        st.plotly_chart(fig_freq, use_container_width=True)

        st.markdown("""
- <span style='background-color:#ffb3b3'>**Red/Pink**</span>: Team received at least one Awesome Award ("Kudos Corner")
- <span style='background-color:#b3cfff'>**Blue**</span>: Team received only Team Awards
        """, unsafe_allow_html=True)

        # darker highlight colors
        def highlight_award_type(row):
            awesome = row.get('Total Awesome Awards', 0)
            team = row.get('Total Team Awards', 0)
            if awesome > 0:
                return ['background-color: #ffb3b3; color: #111827'] * len(row)
            elif team > 0:
                return ['background-color: #b3cfff; color: #111827'] * len(row)
            else:
                return [''] * len(row)

        st.dataframe(
            freq_df.style.apply(highlight_award_type, axis=1),
            use_container_width=True
        )

    # -------- Line charts (after table) --------
    if trend_all is not None and not trend_all.empty:
        st.subheader("All Hands – Team & Awesome Awards")
        fig_all = px.line(
            trend_all, x='Period', y='Award_Count',
            color='Team name', symbol='Award_Type',
            markers=True,
            title="All Hands Team & Awesome Awards – Team-Level Trends Over Time",
            line_dash='Award_Type',
            color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
        )
        if time_period == "Monthly":
            fig_all.update_xaxes(
                dtick="M1",
                tickformat="%b %Y",
                tickangle=45,
                tickvals=trend_all['Period'].drop_duplicates()
            )
        elif time_period == "Quarterly":
            fig_all.update_xaxes(
                dtick="Q1",
                tickformat="Q%q %Y",
                tickangle=45,
                tickvals=trend_all['Period'].drop_duplicates()
            )
        else:
            fig_all.update_xaxes(
                dtick="Y1",
                tickformat="%Y",
                tickangle=45,
                tickvals=trend_all['Period'].drop_duplicates()
            )
        fig_all.update_layout(
            xaxis_title='Time Period',
            yaxis_title='Number of Awards',
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig_all, use_container_width=True)
    else:
        st.info("No All Hands data for selected filters.")

    if trend_kudos is not None and not trend_kudos.empty:
        st.subheader("Kudos Corner – Team & Awesome Awards")
        fig_kudos = px.line(
            trend_kudos, x='Period', y='Award_Count',
            color='Team name', symbol='Award_Type',
            markers=True,
            title="Kudos Corner Team & Awesome Awards – Team-Level Trends Over Time",
            line_dash='Award_Type',
            color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
        )
        if time_period == "Monthly":
            fig_kudos.update_xaxes(
                dtick="M1",
                tickformat="%b %Y",
                tickangle=45,
                tickvals=trend_kudos['Period'].drop_duplicates()
            )
        elif time_period == "Quarterly":
            fig_kudos.update_xaxes(
                dtick="Q1",
                tickformat="Q%q %Y",
                tickangle=45,
                tickvals=trend_kudos['Period'].drop_duplicates()
            )
        else:
            fig_kudos.update_xaxes(
                dtick="Y1",
                tickformat="%Y",
                tickangle=45,
                tickvals=trend_kudos['Period'].drop_duplicates()
            )
        fig_kudos.update_layout(
            xaxis_title='Time Period',
            yaxis_title='Number of Awards',
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig_kudos, use_container_width=True)
    else:
        st.info("No Kudos Corner data for selected filters.")

# -----------------------
# Entrypoint
# -----------------------
if __name__ == "__main__":
    show_recognition_team_tab()
