import streamlit as st
import pandas as pd
import plotly.express as px
import re
import html

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
    """Auto-detect the amount column by common names or heuristics."""
    candidates = [
        "Coupon Amount", "Coupon Amount (₹)", "Coupon amount",
        "Coupon", "Amount", "Budget", "Allocation",
        "Award Amount", "Award_Value", "CouponValue", "Coupon_Value"
    ]
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            return lower_cols[cand.lower()]
    # heuristic fallback
    for c in df.columns:
        lc = c.lower()
        if any(k in lc for k in ["coupon", "amount", "allocation", "budget"]):
            return c
    return None

def _to_number(series: pd.Series) -> pd.Series:
    """
    Safe currency parser:
    - strips ₹ and commas
    - extracts first numeric token like -1234.56
    - returns 0.0 if none found
    """
    s = series.astype(str)
    s = s.str.replace("\u20b9", "", regex=False)  # ₹
    s = s.str.replace(",", "", regex=False)
    s = s.str.strip()
    extracted = s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce").fillna(0.0)

def _fmt_currency(x: float) -> str:
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return "₹0"

def _metric_with_hover(label: str, value: str, tooltip: str):
    """
    Render a KPI-like tile with a native browser tooltip (title attr).
    """
    safe_tooltip = html.escape(tooltip).replace("\n", "&#10;")
    st.markdown(
        f"""
<div title="{safe_tooltip}" style="
    border:1px solid #eee; border-radius:10px; padding:12px 16px;
    background:#fafafa;">
  <div style="font-size:0.9rem; color:#6b7280;">{html.escape(label)}</div>
  <div style="font-size:1.6rem; font-weight:700; color:#111827;">{html.escape(value)}</div>
  <div style="font-size:0.75rem; color:#9CA3AF;">Hover for breakdown</div>
</div>
""",
        unsafe_allow_html=True,
    )

# -----------------------
# Load & preprocess
# -----------------------
def load_and_process_data():
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df = pd.read_excel(url)

    # Month/Year -> Date
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].astype(str).str.strip().str.capitalize()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['Month_Num'] = df['Month'].map(month_map)
    df['Date'] = pd.to_datetime(dict(year=df['year'], month=df['Month_Num'], day=1), errors='coerce')

    # Normalize team names
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

    # Robust Amount column
    amt_col = _find_amount_col(df)
    df['Amount'] = _to_number(df[amt_col]) if amt_col else 0.0

    return df

# -----------------------
# Trend builder
# -----------------------
def build_award_trend(
    df, award_types, selected_years, time_period,
    team_mode, selected_team, top_team_count, kudos_corner=False
):
    dfs = []

    # Kudos Corner filter tolerant to 'Nominated' field variants
    if kudos_corner:
        nom_col = next((c for c in ['Nominated', 'Nominated In', 'NominatedIn'] if c in df.columns), None)
        if nom_col:
            df = df[df[nom_col].astype(str).str.contains("kudos", case=False, na=False)]

    # TEAM AWARD
    if "Team Award" in award_types:
        team_award_df = df[df['New_Award_title'] == 'Team Award'].copy()
        teams = sorted(team_award_df['Team name'].dropna().unique())

        if team_mode == "All Teams":
            active_teams = teams
        elif team_mode == "Single Team":
            active_teams = [selected_team] if (selected_team and selected_team != "All Teams") else teams
        elif team_mode == "Top Teams":
            top_teams = team_award_df['Team name'].value_counts().head(top_team_count).index.tolist()
            active_teams = top_teams

        filtered = team_award_df[
            (team_award_df['year'].isin(selected_years)) &
            (team_award_df['Team name'].isin(active_teams))
        ].copy()
        filtered['Award_Type'] = 'Team Award'
        dfs.append(filtered)

    # AWESOME AWARD restricted to Greenmath/Edgecore employee teams
    if "Awesome Award" in award_types:
        greenmath_employees = df[df['Team name'].str.contains('green', case=False, na=False)]
        edgecore_employees = df[df['Team name'].str.contains('edgecore', case=False, na=False)]
        filtered_employees = pd.concat([greenmath_employees, edgecore_employees], ignore_index=True)
        filtered_employees = filtered_employees[['Employee Name', 'Team name']].drop_duplicates()

        awesome_awards_raw = df[df['New_Award_title'] == 'Awesome Award'].copy()
        mapped = awesome_awards_raw.merge(
            filtered_employees, on='Employee Name', how='left', suffixes=('', '_emp')
        )
        mapped['Team name Final'] = mapped['Team name_emp'].fillna(mapped['Team name'])
        mapped = mapped[
            mapped['Team name Final'].str.contains('green|edgecore', case=False, na=False) &
            mapped['year'].isin(selected_years)
        ].copy()
        mapped['Team name'] = mapped['Team name Final']
        mapped.drop(columns=['Team name_emp', 'Team name Final'], errors='ignore', inplace=True)
        mapped['Award_Type'] = 'Awesome Award'
        dfs.append(mapped)

    if not dfs:
        return None, None

    combined_df = pd.concat(dfs, ignore_index=True)

    # Period
    if time_period == "Monthly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        combined_df['Period'] = combined_df['Date'].dt.to_period('Y').dt.to_timestamp()

    trend_df = (
        combined_df
        .groupby(['Period', 'Team name', 'Award_Type'], as_index=False)
        .size()
        .rename(columns={'size': 'Award_Count'})
    )
    return trend_df, combined_df

# -----------------------
# KPIs (Awards Count has hover tooltip)
# -----------------------
def display_budget_kpis(filtered_df: pd.DataFrame):
    total_amount = float(filtered_df['Amount'].sum()) if 'Amount' in filtered_df.columns else 0.0
    total_awards = int(len(filtered_df))
    avg_amount = (total_amount / total_awards) if total_awards > 0 else 0.0
    team_counts = int(filtered_df['Team name'].nunique())

    # Top team by allocation
    if total_awards > 0 and 'Amount' in filtered_df.columns:
        by_team = filtered_df.groupby('Team name', as_index=False)['Amount'].sum()
        if not by_team.empty:
            top_row = by_team.sort_values('Amount', ascending=False).iloc[0]
            top_team = str(top_row['Team name'])
            top_amt = float(top_row['Amount'])
            share = (top_amt / total_amount * 100.0) if total_amount > 0 else 0.0
        else:
            top_team, top_amt, share = "—", 0.0, 0.0
    else:
        top_team, top_amt, share = "—", 0.0, 0.0

    # Build tooltip breakdown for Awards Count: by New_Award_title
    if 'New_Award_title' in filtered_df.columns and total_awards > 0:
        counts = (
            filtered_df['New_Award_title']
            .fillna('Unknown')
            .value_counts()
            .sort_values(ascending=False)
        )
        lines = [f"{k}: {v}" for k, v in counts.items()]
        tooltip_text = "Awards breakdown\\n" + "\\n".join(lines[:25])  # keep tooltip compact
    else:
        tooltip_text = "Awards breakdown\\nNo awards in current filters."

    # Layout: put 5 tiles; the 3rd (Awards Count) is hover-enabled
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Allocation", _fmt_currency(total_amount))
    with c2:
        st.metric("Avg per Award", _fmt_currency(avg_amount))
    with c3:
        _metric_with_hover("Awards Count", f"{total_awards}", tooltip_text)
    with c4:
        st.metric("Active Teams", f"{team_counts}")
    with c5:
        st.metric("Top Team by Allocation", top_team, delta=f"{share:.1f}% share")

# -----------------------
# Allocation chart
# -----------------------
def plot_team_allocation(total_df, stack_by_award=False, top_n=10, title_suffix=""):
    df = total_df.dropna(subset=['Team name']).copy()
    if df.empty:
        st.info("No allocation data for current filters.")
        return

    if 'Amount' not in df.columns:
        st.info("Amount column missing after parsing; showing nothing.")
        return

    if stack_by_award:
        agg = (
            df.groupby(['Team name', 'Award_Type'], as_index=False)['Amount']
              .sum()
              .sort_values('Amount', ascending=False)
        )
        top_teams = (
            agg.groupby('Team name', as_index=False)['Amount'].sum()
               .sort_values('Amount', ascending=False)['Team name']
               .head(top_n)
               .tolist()
        )
        agg = agg[agg['Team name'].isin(top_teams)]
        fig = px.bar(
            agg, x='Team name', y='Amount', color='Award_Type',
            title=f"Top {top_n} Teams by Total Allocation {title_suffix}",
            barmode='stack', text_auto='.2s'
        )
    else:
        agg = (
            df.groupby('Team name', as_index=False)['Amount']
              .sum()
              .sort_values('Amount', ascending=False)
              .head(top_n)
        )
        fig = px.bar(
            agg, x='Team name', y='Amount',
            title=f"Top {top_n} Teams by Total Allocation {title_suffix}",
            text_auto='.2s'
        )

    fig.update_layout(
        xaxis_title='Team',
        yaxis_title='Total Allocation (₹)',
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)

    if not stack_by_award:
        st.dataframe(
            agg.rename(columns={'Amount': 'Total Allocation (₹)'}),
            use_container_width=True
        )

# -----------------------
# UI
# -----------------------
def show_recognition_team_tab():
    df = load_and_process_data()
    st.title("Team & Awesome Awards Trends")

    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 2])
        with col1:
            period_options = ["Monthly", "Quarterly", "Yearly"]
            time_period = st.selectbox("Select Period", period_options, index=0)
        with col2:
            years = sorted(df['year'].dropna().unique())
            default_years = years[-2:] if len(years) >= 2 else years
            selected_years = st.multiselect("Year(s)", years, default=default_years)
        with col3:
            award_types = st.multiselect(
                "Select Award Type(s)",
                ["Team Award", "Awesome Award"],
                default=["Team Award", "Awesome Award"]
            )
        with col4:
            team_mode = st.selectbox("Display Teams by", ["All Teams", "Top Teams", "Single Team"], index=1)
        with col5:
            teams = sorted(df['Team name'].dropna().unique())
            top_team_count = st.slider(
                "No. Top Teams",
                min_value=5,
                max_value=min(20, len(teams)) if len(teams) else 5,
                value=min(10, len(teams)) if len(teams) else 5
            ) if team_mode == "Top Teams" else None
        with col6:
            kudos_filter = st.checkbox("Kudos Corner", value=False)

        selected_team = st.selectbox("Select Team", ["All Teams"] + teams) if team_mode == "Single Team" else None

    trend_df, filtered_df = build_award_trend(
        df, award_types, selected_years, time_period,
        team_mode, selected_team, top_team_count,
        kudos_corner=kudos_filter
    )

    if trend_df is None or trend_df.empty:
        st.warning("No data for selected filters.")
        return

    # ---- KPIs (Awards Count hover-enabled) ----
    display_budget_kpis(filtered_df)

    # Trend line
    fig = px.line(
        trend_df, x='Period', y='Award_Count',
        color='Team name', symbol='Award_Type',
        markers=True, title="Award Trends Over Time",
        line_dash='Award_Type',
        color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
    )
    if time_period == "Monthly":
        fig.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=45, tickvals=trend_df['Period'].drop_duplicates())
    elif time_period == "Quarterly":
        fig.update_xaxes(dtick="Q1", tickformat="Q%q %Y", tickangle=45, tickvals=trend_df['Period'].drop_duplicates())
    else:
        fig.update_xaxes(dtick="Y1", tickformat="%Y", tickangle=45, tickvals=trend_df['Period'].drop_duplicates())
    fig.update_layout(xaxis_title='Time Period', yaxis_title='Number of Awards', hovermode='x unified', template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    # Allocation
    st.subheader("Top Teams by Total Allocation")
    colA, colB = st.columns([2, 1])
    with colA:
        stack_view = st.checkbox("Stack by Award Type", value=False)
    with colB:
        top_n = st.slider("Show Top N Teams", min_value=5, max_value=20, value=10, step=1)

    suffix = ""
    if selected_years:
        yr_label = ", ".join([str(int(y)) for y in selected_years if pd.notna(y)])
        suffix = f"({yr_label})"

    plot_team_allocation(filtered_df, stack_by_award=stack_view, top_n=top_n, title_suffix=f" {suffix}")

# -----------------------
# Entrypoint
# -----------------------
if __name__ == "__main__":
    show_recognition_team_tab()
