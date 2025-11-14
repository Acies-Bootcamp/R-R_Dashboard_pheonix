import streamlit as st
import pandas as pd
import plotly.express as px
import re
import html
from utils import load_css        # ⭐ GLOBAL CSS THEME

# ============================================================
# GLASS CARD HELPERS
# ============================================================
def chart_card_start(title):
    st.markdown(
        f"""
        <div class='glass-card' style='padding:20px; margin-top:18px;'>
            <h3 style="margin-bottom:10px;">{title}</h3>
        """,
        unsafe_allow_html=True
    )

def chart_card_end():
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def normalize_name(name):
    if pd.isna(name): 
        return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name


def _find_amount_col(df):
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


def _to_number(series):
    s = series.astype(str)
    s = s.str.replace("\u20b9", "", regex=False)  # ₹
    s = s.str.replace(",", "", regex=False)
    s = s.str.strip()
    extracted = s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(extracted, errors="coerce").fillna(0.0)


def _fmt_currency(x):
    try:
        return f"₹{x:,.0f}"
    except:
        return "₹0"


def _metric_with_hover(label, value, tooltip):
    safe_tooltip = html.escape(tooltip).replace("\n", "&#10;")
    st.markdown(
        f"""
<div title="{safe_tooltip}" style="
    border:1px solid #eee; border-radius:10px; padding:12px 16px;
    background:rgba(255,255,255,0.55); backdrop-filter: blur(6px);">
  <div style="font-size:0.9rem; color:#6b7280;">{html.escape(label)}</div>
  <div style="font-size:1.6rem; font-weight:700; color:#111827;">{html.escape(value)}</div>
  <div style="font-size:0.75rem; color:#9CA3AF;">Hover for breakdown</div>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# LOAD DATA
# ============================================================
def load_and_process_data():
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df = pd.read_excel(url)

    # Month → number
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

    # Amount column
    amt_col = _find_amount_col(df)
    df['Amount'] = _to_number(df[amt_col]) if amt_col else 0.0

    return df


# ============================================================
# TREND BUILDER
# ============================================================
def build_award_trend(df, award_types, selected_years, time_period, team_mode, selected_team, top_team_count, kudos_corner=False):
    dfs = []

    if kudos_corner:
        nom_col = next((c for c in ["Nominated", "Nominated In", "NominatedIn"] if c in df.columns), None)
        if nom_col:
            df = df[df[nom_col].astype(str).str.contains("kudos", case=False, na=False)]

    # Team Award
    if "Team Award" in award_types:
        team_df = df[df["New_Award_title"] == "Team Award"].copy()
        teams_list = sorted(team_df["Team name"].dropna().unique())

        if team_mode == "All Teams":
            active_teams = teams_list
        elif team_mode == "Single Team":
            active_teams = [selected_team] if selected_team != "All Teams" else teams_list
        elif team_mode == "Top Teams":
            top_teams = team_df["Team name"].value_counts().head(top_team_count).index.tolist()
            active_teams = top_teams

        filtered = team_df[
            (team_df["year"].isin(selected_years)) &
            (team_df["Team name"].isin(active_teams))
        ].copy()
        filtered["Award_Type"] = "Team Award"
        dfs.append(filtered)

    # Awesome Award
    if "Awesome Award" in award_types:
        greenmath_employees = df[df["Team name"].str.contains("green", case=False, na=False)]
        edgecore_employees = df[df["Team name"].str.contains("edgecore", case=False, na=False)]
        filtered_emp = pd.concat([greenmath_employees, edgecore_employees]).drop_duplicates(subset=["Employee Name"])

        awesome = df[df["New_Award_title"] == "Awesome Award"].copy()
        merged = awesome.merge(filtered_emp[["Employee Name", "Team name"]], on="Employee Name", how="left", suffixes=("", "_emp"))

        merged["Team name Final"] = merged["Team name_emp"].fillna(merged["Team name"])
        merged = merged[
            merged["Team name Final"].str.contains("green|edgecore", case=False, na=False) &
            merged["year"].isin(selected_years)
        ].copy()

        merged["Team name"] = merged["Team name Final"]
        merged["Award_Type"] = "Awesome Award"
        dfs.append(merged)

    if not dfs:
        return None, None

    combined_df = pd.concat(dfs, ignore_index=True)

    # Period
    if time_period == "Monthly":
        combined_df["Period"] = combined_df["Date"].dt.to_period("M").dt.to_timestamp()
    elif time_period == "Quarterly":
        combined_df["Period"] = combined_df["Date"].dt.to_period("Q").dt.to_timestamp()
    else:
        combined_df["Period"] = combined_df["Date"].dt.to_period("Y").dt.to_timestamp()

    trend_df = (
        combined_df
        .groupby(["Period", "Team name", "Award_Type"], as_index=False)
        .size()
        .rename(columns={"size": "Award_Count"})
    )

    return trend_df, combined_df


# ============================================================
# KPI CARDS
# ============================================================
def display_budget_kpis(filtered_df):
    total_amount = float(filtered_df["Amount"].sum()) if "Amount" in filtered_df.columns else 0.0
    total_awards = len(filtered_df)
    avg_amt = (total_amount / total_awards) if total_awards else 0.0
    team_count = filtered_df["Team name"].nunique()

    # Top team
    if total_awards and "Amount" in filtered_df.columns:
        grouped = filtered_df.groupby("Team name")["Amount"].sum().sort_values(ascending=False)
        if not grouped.empty:
            top_team = grouped.index[0]
            top_amt = grouped.iloc[0]
            share = (top_amt / total_amount) * 100 if total_amount else 0
        else:
            top_team, top_amt, share = "—", 0, 0
    else:
        top_team, top_amt, share = "—", 0, 0

    # Tooltip breakdown
    if "New_Award_title" in filtered_df.columns and total_awards:
        counts = filtered_df["New_Award_title"].value_counts()
        tooltip = "Awards Breakdown\n" + "\n".join([f"{k}: {v}" for k, v in counts.items()][:25])
    else:
        tooltip = "No award breakdown data."

    # ⭐ Glass-card wrapped KPI section
    chart_card_start("📊 Team Award KPIs")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Allocation", _fmt_currency(total_amount))
    with c2:
        st.metric("Avg per Award", _fmt_currency(avg_amt))
    with c3:
        _metric_with_hover("Awards Count", f"{total_awards}", tooltip)
    with c4:
        st.metric("Active Teams", f"{team_count}")
    with c5:
        st.metric("Top Team", top_team, delta=f"{share:.1f}% share")

    chart_card_end()


# ============================================================
# ALLOCATION BAR CHART
# ============================================================
def plot_team_allocation(total_df, stack=False, top_n=10, title_suffix=""):
    if total_df.empty:
        st.info("No allocation data.")
        return

    df = total_df.copy()

    chart_card_start("🏢 Team Allocation Overview")

    if stack:
        agg = (
            df.groupby(["Team name", "Award_Type"])["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
        )
        top_teams = (
            agg.groupby("Team name")["Amount"].sum().sort_values(ascending=False).head(top_n).index
        )
        agg = agg[agg["Team name"].isin(top_teams)]

        fig = px.bar(
            agg, x="Team name", y="Amount",
            color="Award_Type", barmode="stack",
            title=f"Top {top_n} Teams by Allocation {title_suffix}",
            text_auto=".2s"
        )
    else:
        agg = (
            df.groupby("Team name")["Amount"]
            .sum().reset_index()
            .sort_values("Amount", ascending=False)
            .head(top_n)
        )
        fig = px.bar(
            agg, x="Team name", y="Amount",
            title=f"Top {top_n} Teams by Allocation {title_suffix}",
            text_auto=".2s"
        )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="Team",
        yaxis_title="Total Allocation (₹)"
    )
    st.plotly_chart(fig, use_container_width=True)

    if not stack:
        st.dataframe(
            agg.rename(columns={"Amount": "Total Allocation (₹)"}),
            use_container_width=True
        )

    chart_card_end()


# ============================================================
# MAIN TEAM TAB
# ============================================================
def show_recognition_team_tab():

    load_css()          # ⭐ Global styling

    df = load_and_process_data()
    st.title("🏆 Team & Awesome Awards Analysis")

    # ---------------- FILTERS ----------------
    chart_card_start("🎯 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        time_period = st.selectbox("Period", ["Monthly", "Quarterly", "Yearly"], index=0)

    with col2:
        years = sorted(df["year"].dropna().unique())
        selected_years = st.multiselect("Year(s)", years, default=years[-2:])

    with col3:
        award_types = st.multiselect(
            "Award Types",
            ["Team Award", "Awesome Award"],
            default=["Team Award", "Awesome Award"]
        )

    with col4:
        team_mode = st.selectbox("Team Display", ["All Teams", "Top Teams", "Single Team"])

    teams = sorted(df["Team name"].dropna().unique())

    colA, colB = st.columns([2, 1])
    with colA:
        if team_mode == "Top Teams":
            top_team_count = st.slider("Select N Top Teams", 5, 20, 10)
        else:
            top_team_count = None

    with colB:
        if team_mode == "Single Team":
            selected_team = st.selectbox("Choose Team", ["All Teams"] + teams)
        else:
            selected_team = None

    kudos_filter = st.checkbox("Filter: Kudos Corner", value=False)

    chart_card_end()

    # ---------------- BUILD TREND ----------------
    trend_df, filtered_df = build_award_trend(
        df, award_types, selected_years, time_period,
        team_mode, selected_team, top_team_count,
        kudos_corner=kudos_filter
    )

    if trend_df is None or trend_df.empty:
        st.warning("No data found for the selected filters.")
        return

    # ---------------- KPIs ----------------
    display_budget_kpis(filtered_df)

    # ---------------- LINE CHART ----------------
    chart_card_start("📈 Team Award Trends Over Time")

    fig = px.line(
        trend_df,
        x="Period", y="Award_Count",
        color="Team name",
        symbol="Award_Type",
        line_dash="Award_Type",
        markers=True,
        title="Team Recognition Trend"
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        xaxis_title="Time",
        yaxis_title="Awards Count"
    )

    st.plotly_chart(fig, use_container_width=True)
    chart_card_end()

    # ---------------- ALLOCATION ----------------
    chart_card_start("💰 Budget Allocation by Team")

    colX, colY = st.columns([2, 1])
    with colX:
        stack = st.checkbox("Stack by Award Type")
    with colY:
        top_n = st.slider("Show Top N Teams", 5, 20, 10)

    suffix = ""
    if selected_years:
        suffix = "(" + ", ".join([str(int(y)) for y in selected_years]) + ")"

    plot_team_allocation(filtered_df, stack=stack, top_n=top_n, title_suffix=suffix)

    chart_card_end()


# ============================================================
# Standalone
# ============================================================
if __name__ == "__main__":
    show_recognition_team_tab()
