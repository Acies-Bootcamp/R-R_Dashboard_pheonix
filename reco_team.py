import streamlit as st
import styles
import pandas as pd
import plotly.express as px
import re
import html


# -----------------------
# Global Glass / KPI CSS
# -----------------------
glass_css = """
<style>
/* KPI cards: semi‑transparent frosted glass that harmonises with the global palette */
.metric-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12);
  text-align: center;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
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
  color: #0D3C66;
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

/* Chart container */
.stPlotlyChart {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* Table header */
.dataframe th {
  background-color: rgba(255, 255, 255, 0.6) !important;
  color: #0D3C66 !important;
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
    s = s.str.replace("\u20b9", "", regex=False)
    s = s.str.replace(",", "", regex=False)
    s = s.str.strip()
    extracted = s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce").fillna(0.0)


def load_and_process_data():
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df = pd.read_excel(url)

    df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    df = df[df['year'] > 0]

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].astype(str).str.strip().str.capitalize()
    df['Month_Num'] = df['Month'].map(month_map)
    df['Date'] = pd.to_datetime(
        dict(year=df['year'], month=df['Month_Num'], day=1),
        errors='coerce'
    )

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

    df = df[
        (df['Team name'].notna()) &
        (df['Team name'].astype(str).str.strip() != '') &
        (~df['Team name'].astype(str).str.strip().str.lower().isin(['nan', 'none', 'null', 'unknown', 'unknown team'])) &
        (~df['Team name'].astype(str).str.lower().str.contains('unknown', na=False))
    ].copy()

    amt_col = _find_amount_col(df)
    df['Amount'] = _to_number(df[amt_col]) if amt_col else 0.0

    return df


def clean_teamname_df(df, column='Team name'):
    if df.empty:
        return df
    
    df_cleaned = df.copy()
    df_cleaned = df_cleaned[df_cleaned[column].notna()].copy()
    df_cleaned = df_cleaned[df_cleaned[column].astype(str).str.strip() != ''].copy()
    
    return df_cleaned


# -----------------------
# KPIs
# -----------------------
def display_team_level_kpis(
    df_allhands: pd.DataFrame, 
    df_kudos: pd.DataFrame,
    selected_years,
    team_mode,
    selected_team,
    top_team_count,
    freq_award_filter: list,
    df_original: pd.DataFrame
):
    """Display KPIs - react to award filter"""
    
    df_original_filtered = df_original[df_original['year'].isin(selected_years)].copy()
    total_teams_overall = int(df_original_filtered['Team name'].nunique())
    
    df_allhands = df_allhands[df_allhands['year'].isin(selected_years)] if df_allhands is not None and not df_allhands.empty else pd.DataFrame()
    df_kudos = df_kudos[df_kudos['year'].isin(selected_years)] if df_kudos is not None and not df_kudos.empty else pd.DataFrame()
    
    if freq_award_filter:
        df_allhands = df_allhands[df_allhands['New_Award_title'].isin(freq_award_filter)] if not df_allhands.empty else pd.DataFrame()
        df_kudos = df_kudos[df_kudos['New_Award_title'].isin(freq_award_filter)] if not df_kudos.empty else pd.DataFrame()
    
    df_allhands_clean = clean_teamname_df(df_allhands) if not df_allhands.empty else pd.DataFrame()
    df_kudos_clean = clean_teamname_df(df_kudos) if not df_kudos.empty else pd.DataFrame()
    
    if team_mode == "Single Team" and selected_team and selected_team != "All Teams":
        df_allhands_clean = df_allhands_clean[df_allhands_clean['Team name'] == selected_team]
        df_kudos_clean = df_kudos_clean[df_kudos_clean['Team name'] == selected_team]
    elif team_mode == "Most Couponed Teams" and top_team_count:
        combined = pd.concat([df_allhands_clean, df_kudos_clean])
        top_teams = combined['Team name'].value_counts().head(top_team_count).index.tolist()
        df_allhands_clean = df_allhands_clean[df_allhands_clean['Team name'].isin(top_teams)]
        df_kudos_clean = df_kudos_clean[df_kudos_clean['Team name'].isin(top_teams)]
    
    distinct_all = int(df_allhands_clean['Team name'].nunique()) if not df_allhands_clean.empty else 0
    distinct_kudos = int(df_kudos_clean['Team name'].nunique()) if not df_kudos_clean.empty else 0

    def avg_teams_per_month(df: pd.DataFrame) -> int:
        if df is None or df.empty or 'Date' not in df.columns:
            return 0
        monthly = df.groupby(df['Date'].dt.to_period('M'))['Team name'].nunique()
        if monthly.empty:
            return 0
        return int(round(monthly.mean()))

    avg_month_all = avg_teams_per_month(df_allhands_clean)
    avg_month_kudos = avg_teams_per_month(df_kudos_clean)
    total_awards = len(df_allhands_clean) + len(df_kudos_clean)

    st.subheader("Team Recognition KPIs")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Distinct Teams (All Hands)
                    <span class="kpi-help" title="Number of unique teams for the selected award types and filters in All Hands.">?</span>
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
                    Distinct Teams (Kudos Corner)
                    <span class="kpi-help" title="Number of unique teams for the selected award types and filters in Kudos Corner.">?</span>
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
                    Total Teams Overall
                    <span class="kpi-help" title="Total number of unique valid teams in the selected year(s).">?</span>
                  </span>
                </h4>
                <h2>{total_teams_overall}</h2>
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
                    Avg Teams/Month (All Hands)
                    <span class="kpi-help" title="Average number of unique teams per month in All Hands for selected filters.">?</span>
                  </span>
                </h4>
                <h2>{avg_month_all}</h2>
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
                    Avg Teams/Month (Kudos Corner)
                    <span class="kpi-help" title="Average number of unique teams per month in Kudos Corner for selected filters.">?</span>
                  </span>
                </h4>
                <h2>{avg_month_kudos}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c6:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>
                  <span class="kpi-label">
                    Total Awards Distributed
                    <span class="kpi-help" title="Total awards distributed across all types (Team, Spot, Champion, Awesome).">?</span>
                  </span>
                </h4>
                <h2>{total_awards}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.caption("**Note:** All KPIs react to the selected award types and filters.")


# -----------------------
# Team frequency table
# -----------------------
def build_team_frequency_table(
    df: pd.DataFrame,
    selected_years,
    team_mode,
    selected_team,
    top_team_count,
    freq_award_filter: list,
    employee_team_map=None
):
    df_freq = df[df['year'].isin(selected_years)].copy()
    
    if freq_award_filter:
        df_freq = df_freq[df_freq['New_Award_title'].isin(freq_award_filter)]
    
    df_freq = clean_teamname_df(df_freq, column='Team name')

    if employee_team_map is not None and not employee_team_map.empty:
        awesome_award_rows = df_freq[df_freq['New_Award_title'] == 'Awesome Award'].copy()
        if not awesome_award_rows.empty:
            mapped = awesome_award_rows.merge(
                employee_team_map, on='Employee Name', how='left', suffixes=('', '_mapped')
            )
            mapped['Team name'] = mapped['Team name_mapped'].fillna(mapped['Team name'])
            if 'Team name_mapped' in mapped.columns:
                mapped = mapped.drop(columns=['Team name_mapped'])
            non_awesome = df_freq[df_freq['New_Award_title'] != 'Awesome Award'].copy()
            df_freq = pd.concat([non_awesome, mapped], ignore_index=True)

    if df_freq.empty:
        return pd.DataFrame(columns=[
            "Team",
            "No. of distinct people",
            "Total Coupons",
            "Total Team Awards",
            "Total Spot Awards",
            "Total Champion Awards",
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
            "No. of distinct people",
            "Total Coupons",
            "Total Team Awards",
            "Total Spot Awards",
            "Total Champion Awards",
            "Total Awesome Awards",
        ])

    grouped = df_freq.groupby('Team name').agg(
        distinct_people=('Employee Name', 'nunique'),
        times_awarded=('New_Award_title', 'size'),
        total_team_awards=('New_Award_title', lambda s: (s == 'Team Award').sum()),
        total_spot_awards=('New_Award_title', lambda s: (s == 'Spot Award').sum()),
        total_champion_awards=('New_Award_title', lambda s: (s == 'Champion Award').sum()),
        total_awesome_awards=('New_Award_title', lambda s: (s == 'Awesome Award').sum()),
    ).reset_index()

    grouped['total_awards_internal'] = (
        grouped['total_team_awards'] + 
        grouped['total_spot_awards'] + 
        grouped['total_champion_awards'] +
        grouped['total_awesome_awards']
    )
    
    grouped = grouped.sort_values('total_awards_internal', ascending=False)

    grouped = grouped.rename(columns={
        'Team name': 'Team',
        'distinct_people': 'No. of distinct people',
        'times_awarded': 'Total Coupons',
        'total_team_awards': 'Total Team Awards',
        'total_spot_awards': 'Total Spot Awards',
        'total_champion_awards': 'Total Champion Awards',
        'total_awesome_awards': 'Total Awesome Awards',
    })

    grouped = grouped.drop(columns=['total_awards_internal'])

    return grouped


# -----------------------
# LINE CHARTS
# -----------------------
def build_allhands_trend(df_allhands, selected_years, time_period):
    df_filtered = df_allhands[
        (df_allhands['New_Award_title'].isin(['Team Award', 'Champion Award'])) &
        (df_allhands['year'].isin(selected_years))
    ].copy()
    df_filtered = clean_teamname_df(df_filtered, column='Team name')
    
    if df_filtered.empty:
        return None
    
    if time_period == "Monthly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Y').dt.to_timestamp()
    
    df_filtered = df_filtered.dropna(subset=['Period'])
    
    trend_df = (
        df_filtered
        .groupby(['Period', 'Team name'], as_index=False)
        .size()
        .rename(columns={'size': 'Total_Awards'})
    )
    
    return trend_df


def build_kudos_trend(df_kudos, selected_years, time_period, employee_team_map):
    dfs = []
    
    product_teams = ['Greenmath', 'Edgecore']
    product_df = df_kudos[
        (df_kudos['Team name'].isin(product_teams)) &
        (df_kudos['New_Award_title'].isin(['Team Award', 'Spot Award', 'Champion Award', 'Awesome Award'])) &
        (df_kudos['year'].isin(selected_years))
    ].copy()
    product_df = clean_teamname_df(product_df, column='Team name')
    if not product_df.empty:
        dfs.append(product_df)
    
    other_df = df_kudos[
        (~df_kudos['Team name'].isin(product_teams)) &
        (df_kudos['New_Award_title'].isin(['Team Award', 'Champion Award'])) &
        (df_kudos['year'].isin(selected_years))
    ].copy()
    other_df = clean_teamname_df(other_df, column='Team name')
    if not other_df.empty:
        dfs.append(other_df)
    
    if not dfs:
        return None
    
    df_filtered = pd.concat(dfs, ignore_index=True)
    
    if time_period == "Monthly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Y').dt.to_timestamp()
    
    df_filtered = df_filtered.dropna(subset=['Period'])
    
    trend_df = (
        df_filtered
        .groupby(['Period', 'Team name'], as_index=False)
        .size()
        .rename(columns={'size': 'Total_Awards'})
    )
    
    return trend_df


# -----------------------
# Main UI
# -----------------------
def show_recognition_team_tab():
    theme = st.session_state.get("theme", "White")
    styles.apply_styles(theme=theme)
    st.markdown(glass_css, unsafe_allow_html=True)

    df = load_and_process_data()

    st.title("Team-Level Trends")
    st.caption(
        "These charts show *team-level trends* for **Team Awards**, **Spot Awards**, **Champion Awards**, and **Awesome Awards**. "
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
            time_period = st.selectbox("Select Period", period_options, index=0, key="team_period_select")

        with col2:
            years = sorted(df['year'].dropna().unique())
            year_options = ["All"] + [int(y) for y in years]
            selected_years_raw = st.multiselect(
                "Select Year(s)",
                options=year_options,
                default=["All"],
                key="team_year_multiselect"
            )
            if "All" in selected_years_raw or not selected_years_raw:
                selected_years = [int(y) for y in years]
            else:
                selected_years = [int(y) for y in selected_years_raw if y != "All"]

        with col3:
            team_mode = st.selectbox(
                "Display Teams by",
                ["All Teams", "Most Couponed Teams", "Single Team"],
                index=0,
                key="team_mode_select"
            )

        with col4:
            teams_filtered_by_year = sorted(
                clean_teamname_df(df[df['year'].isin(selected_years)])['Team name'].unique()
            )
            
            if team_mode == "Most Couponed Teams":
                top_team_count = st.slider(
                    "No. of Most Couponed Teams",
                    min_value=5,
                    max_value=min(20, len(teams_filtered_by_year)) if teams_filtered_by_year else 5,
                    value=min(10, len(teams_filtered_by_year)) if teams_filtered_by_year else 5,
                    key="team_top_count_slider"
                )
            else:
                top_team_count = None

        with col5:
            award_options = ["All", "Team Award", "Spot Award", "Champion Award", "Awesome Award"]
            selected_awards = st.multiselect(
                "Award Types",
                options=award_options,
                default=["All"],
                key="team_award_multiselect"
            )
            
            if "All" in selected_awards:
                freq_award_filter = ["Team Award", "Spot Award", "Champion Award", "Awesome Award"]
            else:
                freq_award_filter = selected_awards

        if team_mode == "Single Team":
            selected_team = st.selectbox(
                "Select Team", 
                ["All Teams"] + teams_filtered_by_year,
                key="team_single_select"
            )
        else:
            selected_team = None

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

    # -------- KPIs --------
    display_team_level_kpis(
        df_allhands, 
        df_kudos,
        selected_years,
        team_mode,
        selected_team,
        top_team_count,
        freq_award_filter,
        df
    )

    show_glossary(
        "Team Recognition KPIs",
        "These six metrics provide a snapshot of team-level recognition. "
        "**Distinct Teams** counts unique teams in each system. **Total Teams Overall** shows all valid teams in selected years (excluding Unknown). "
        "**Avg Teams/Month** shows monthly average. **Total Awards Distributed** counts all awards across all types."
    )

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
        st.info("No team recognition data for the selected filters and award types.")
    else:
        freq_chart_df = freq_df.copy()
        freq_chart_df = freq_chart_df.sort_values(
            by=['Total Team Awards', 'Total Spot Awards', 'Total Champion Awards', 'Total Awesome Awards'],
            ascending=True
        )
        
        stacked_data = pd.melt(
            freq_chart_df,
            id_vars=['Team'],
            value_vars=['Total Team Awards', 'Total Spot Awards', 'Total Champion Awards', 'Total Awesome Awards'],
            var_name='Award Type',
            value_name='Count'
        )
        
        stacked_data['Award Type'] = stacked_data['Award Type'].str.replace('Total ', '')
        
        fig_stacked = px.bar(
            stacked_data,
            x='Count',
            y='Team',
            color='Award Type',
            orientation='h',
            title='Team Recognition by Award Type (Stacked)',
            color_discrete_map={
                'Team Awards': '#1E88E5',
                'Spot Awards': '#66BB6A',
                'Champion Awards': '#9C27B0',
                'Awesome Awards': '#FF7043'
            }
        )
        
        fig_stacked.update_layout(
            xaxis_title='Number of Awards',
            yaxis_title='Team',
            template='plotly_white',
            height=max(400, len(freq_chart_df) * 25),
            margin=dict(l=40, r=30, t=60, b=40),
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_stacked, use_container_width=True)

        show_glossary(
            "Team Recognition by Award Type",
            "Stacked bar chart showing total awards per team, broken down by type. "
            "Teams sorted by total count. Colors: Blue (Team), Green (Spot), Purple (Champion), Orange (Awesome)."
        )

        def highlight_award_type(row):
            champion = row.get('Total Champion Awards', 0)
            spot = row.get('Total Spot Awards', 0)
            team = row.get('Total Team Awards', 0)
            
            if champion > 0:
                return ['background-color: #e1bee7; color: #111827'] * len(row)
            elif spot > 0:
                return ['background-color: #d4f4dd; color: #111827'] * len(row)
            elif team > 0:
                return ['background-color: #b3cfff; color: #111827'] * len(row)
            else:
                return [''] * len(row)
        
        st.markdown("""
        <div style='padding: 10px 0; font-size: 14px;'>
        <b>Color Legend:</b><br>
        <span style='background-color: #e1bee7; padding: 3px 8px; border-radius: 4px; margin-right: 6px;'></span>
        Purple: <b>Champion Awards</b><br>
        <span style='background-color: #d4f4dd; padding: 3px 8px; border-radius: 4px; margin-right: 6px;'></span>
        Green: <b>Spot Awards</b><br>
        <span style='background-color: #b3cfff; padding: 3px 8px; border-radius: 4px; margin-right: 6px;'></span>
        Blue: <b>Team Awards only</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.dataframe(
            freq_df.style.apply(highlight_award_type, axis=1),
            use_container_width=True
        )

        show_glossary(
            "Team Frequency Table",
            "Detailed metrics: distinct people, total coupons, breakdowns by type. "
            "Row colors indicate highest award: Purple (Champion), Green (Spot), Blue (Team only)."
        )

    # -------- LINE CHARTS --------
    st.markdown("---")
    st.subheader("Award Trends Over Time")
    
    trend_allhands = build_allhands_trend(df_allhands, selected_years, time_period)
    if trend_allhands is not None and not trend_allhands.empty:
        st.markdown("#### All Hands – Total Team & Champion Awards")
        fig_allhands = px.line(
            trend_allhands, 
            x='Period', 
            y='Total_Awards',
            color='Team name',
            markers=True,
            title="All Hands: Total Team & Champion Awards by Team",
        )

        fig_allhands.update_traces(
            mode="lines+markers",
            line=dict(width=3.5),
            marker=dict(size=9, line=dict(width=1, color="black")),
        )

        if time_period == "Monthly":
            fig_allhands.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=45)
        elif time_period == "Quarterly":
            fig_allhands.update_xaxes(dtick="Q1", tickformat="Q%q %Y", tickangle=45)
        else:
            fig_allhands.update_xaxes(dtick="Y1", tickformat="%Y", tickangle=45)
            
        fig_allhands.update_layout(
            xaxis_title='Time Period',
            yaxis_title='Total Awards',
            hovermode='x unified',
            template='plotly_white',
            height=550
        )
        st.plotly_chart(fig_allhands, use_container_width=True)

        show_glossary(
            "All Hands Award Trend",
            "Combined Team + Champion Awards over time per team. Use period filter to adjust granularity."
        )
    
    trend_kudos = build_kudos_trend(df_kudos, selected_years, time_period, employee_team_map)
    if trend_kudos is not None and not trend_kudos.empty:
        st.markdown("#### Kudos Corner – Total Awards by Team")
        st.caption("*Product teams (Greenmath/Edgecore): All awards | Other teams: Team + Champion only*")
        fig_kudos = px.line(
            trend_kudos, 
            x='Period', 
            y='Total_Awards',
            color='Team name',
            markers=True,
            title="Kudos Corner: Total Awards by Team",
        )

        fig_kudos.update_traces(
            mode="lines+markers",
            line=dict(width=3.5),
            marker=dict(size=9, line=dict(width=1, color="black")),
        )

        if time_period == "Monthly":
            fig_kudos.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=45)
        elif time_period == "Quarterly":
            fig_kudos.update_xaxes(dtick="Q1", tickformat="Q%q %Y", tickangle=45)
        else:
            fig_kudos.update_xaxes(dtick="Y1", tickformat="%Y", tickangle=45)
            
        fig_kudos.update_layout(
            xaxis_title='Time Period',
            yaxis_title='Total Awards',
            hovermode='x unified',
            template='plotly_white',
            height=550
        )
        st.plotly_chart(fig_kudos, use_container_width=True)

        show_glossary(
            "Kudos Corner Award Trend",
            "Product teams: all awards. Other teams: Team + Champion only. Tracks new system performance since June 2025."
        )

    # ============================================================
    # ✅ AWESOME AWARDS - RECIPROCAL NOMINATIONS
    # ============================================================

    st.markdown("---")
    st.header("🔄 Awesome Awards - Reciprocal Nominations")

    # ✅ LOAD FRESH DATA WITHOUT UNKNOWN FILTER
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df_raw = pd.read_excel(url)

    # Get ALL Kudos Corner Awesome Awards (INCLUDING Unknown teams)
    awesome_kudos = df_raw[
        df_raw['New_Award_title'].astype(str).str.lower().str.contains('awesome', na=False) &
        df_raw['Nominated In'].astype(str).str.lower().str.contains('kudos', na=False)
    ].copy()

    if awesome_kudos.empty:
        st.info("No Kudos Corner Awesome Awards found.")
    else:
        # Get type breakdown
        type_counts = awesome_kudos['Type'].value_counts().to_dict()
        
        # Find reciprocals
        def norm(x):
            return str(x).strip().lower()
        
        awesome_kudos['Nominee'] = awesome_kudos['Employee Name'].apply(norm)
        awesome_kudos['Nominator'] = awesome_kudos['Nominated By'].apply(norm)
        
        # Remove invalid
        awesome_kudos = awesome_kudos[
            (awesome_kudos['Nominee'] != '') & 
            (awesome_kudos['Nominator'] != '') &
            (awesome_kudos['Nominee'] != 'nan') &
            (awesome_kudos['Nominator'] != 'nan') &
            (awesome_kudos['Nominee'] != awesome_kudos['Nominator'])
        ]
        
        pairs = set(zip(awesome_kudos['Nominee'], awesome_kudos['Nominator']))
        reciprocal_data = []
        
        for a, b in pairs:
            if (b, a) in pairs and a != b:
                pair_key = tuple(sorted([a, b]))
                if pair_key not in [tuple(sorted([p['Person A'].lower(), p['Person B'].lower()])) for p in reciprocal_data]:
                    a_to_b = awesome_kudos[(awesome_kudos['Nominator'] == a) & (awesome_kudos['Nominee'] == b)]
                    b_to_a = awesome_kudos[(awesome_kudos['Nominator'] == b) & (awesome_kudos['Nominee'] == a)]
                    
                    reciprocal_data.append({
                        'Person A': a.title(),
                        'Person B': b.title(),
                        'A → B Times': len(a_to_b),
                        'B → A Times': len(b_to_a),
                        'Total Mutual': len(a_to_b) + len(b_to_a)
                    })
        
        # KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        
        with k1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>
                    <span class="kpi-label">
                        Total Awesome Awards
                        <span class="kpi-help" title="Total Awesome Awards in Kudos Corner (all types).">?</span>
                    </span>
                    </h4>
                    <h2>{len(awesome_kudos)}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with k2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>
                    <span class="kpi-label">
                        Peer to Peer
                        <span class="kpi-help" title="Awards between peers at the same level.">?</span>
                    </span>
                    </h4>
                    <h2>{type_counts.get('Peer to Peer', 0)}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with k3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>
                    <span class="kpi-label">
                        Mentor to Peer
                        <span class="kpi-help" title="Awards from mentors/seniors to junior peers.">?</span>
                    </span>
                    </h4>
                    <h2>{type_counts.get('Mentor to Peer', 0)}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with k4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h4>
                    <span class="kpi-label">
                        Reciprocal Pairs
                        <span class="kpi-help" title="Number of pairs who nominated each other.">?</span>
                    </span>
                    </h4>
                    <h2>{len(reciprocal_data)}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Reciprocal Table
        st.subheader("Reciprocal Nominations (Who Nominated Each Other)")
        
        if reciprocal_data:
            reciprocal_df = pd.DataFrame(reciprocal_data)
            st.dataframe(reciprocal_df, use_container_width=True, hide_index=True)
            st.caption(f"Found {len(reciprocal_data)} reciprocal pair(s) out of {len(awesome_kudos)} total Awesome Awards")
        else:
            st.success("✅ No reciprocal nominations found - all awards are one-way recognition!")

if __name__ == "__main__":
    show_recognition_team_tab()
