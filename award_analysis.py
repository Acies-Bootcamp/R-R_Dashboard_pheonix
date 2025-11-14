import streamlit as st
import pandas as pd
import plotly.express as px
import re
from utils import load_css   # ⭐ CSS LOADER ADDED


# ==============================
# 🎨 Award Color Palette (Pastel Theme)
# ==============================
AWARD_COLORS = {
    "Team Award": "#A7C7E7",       # Light Blue
    "Spot Award": "#F4C2C2",       # Light Pink
    "Champion Award": "#90EE90",   # Light Green
    "Awesome Award": "#FFFACD",    # Light Yellow
    "Occasional Award": "#D8BFD8"  # Light Purple
}


# ==============================
# 🧩 Helper Functions
# ==============================
def normalize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name


@st.cache_data
def load_data():
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)

    # Clean columns
    df['Month'] = df['Month'].astype(str).str.strip().str.capitalize()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')

    # Map months
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month_Num'] = df['Month'].map(month_map)
    df['Date'] = pd.to_datetime(dict(year=df['year'], month=df['Month_Num'], day=1), errors='coerce')

    # Normalize text
    df['New_Award_title'] = df['New_Award_title'].astype(str).str.title().str.strip()
    df['Team name'] = df['Team name'].astype(str).str.title().str.strip()

    return df


# ==============================
# 🎨 Main Award Analysis Dashboard
# ==============================
def show_award_analysis():

    # ⭐ Load global theme.css (VERY IMPORTANT)
    load_css()

    st.markdown("<h1 style='text-align:center; color:#FFD700;'>🏆 Award Analysis Dashboard</h1>", 
                unsafe_allow_html=True)

    df = load_data()

    # ---------------- FILTERS ----------------
    st.markdown("### 🔍 Filter Options")
    with st.container():
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            period = st.selectbox("Select Period", ["Monthly", "Quarterly", "Yearly"], index=0)

        with col2:
            years = sorted(df['year'].dropna().unique())
            selected_years = st.multiselect("Select Year(s)", years, default=years[-2:])

        with col3:
            award_types = st.multiselect(
                "Select Award Type(s)",
                ["Team Award", "Spot Award", "Champion Award", "Awesome Award", "Occasional Award"],
                default=["Team Award", "Spot Award", "Champion Award"]
            )

        with col4:
            recognition_systems = sorted(df['Nominated In'].dropna().unique())
            selected_sys = st.multiselect("Recognition System", ["All"] + recognition_systems, default=["All"])

        col5, col6 = st.columns(2)

        with col5:
            departments = sorted(df['Department'].dropna().unique())
            selected_dept = st.multiselect("Filter by Department", ["All"] + departments, default=["All"])

        with col6:
            locations = sorted(set(x.replace("Bhive,","Bhive, ") for x in df['Seating Location'].dropna().unique()))
            selected_loc = st.multiselect("Filter by Location", ["All"] + locations, default=["All"])

    # Apply filters
    df_filtered = df[
        (df['year'].isin(selected_years)) &
        (df['New_Award_title'].isin(award_types))
    ].copy()

    if "All" not in selected_sys:
        df_filtered = df_filtered[df_filtered['Nominated In'].isin(selected_sys)]

    if "All" not in selected_dept:
        df_filtered = df_filtered[df_filtered['Department'].isin(selected_dept)]

    if "All" not in selected_loc:
        df_filtered = df_filtered[df_filtered['Seating Location'].isin(selected_loc)]

    # Create period column
    if period == "Monthly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('M').dt.to_timestamp()
    elif period == "Quarterly":
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        df_filtered['Period'] = df_filtered['Date'].dt.to_period('Y').dt.to_timestamp()

    st.divider()

    # =============================
    # 🎯 KPI CARDS
    # =============================
    total_awards = len(df_filtered)
    unique_award_titles = df_filtered['New_Award_title'].nunique()
    top_team = df_filtered['Team name'].value_counts().idxmax() if not df_filtered.empty else "N/A"
    most_common_award = df_filtered['New_Award_title'].value_counts().idxmax() if not df_filtered.empty else "N/A"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
            <div class='glass-card' style='background-color:#A7C7E7; text-align:center;'>
                <h4>Total Awards</h4><h2>{total_awards}</h2>
            </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
            <div class='glass-card' style='background-color:#F4C2C2; text-align:center;'>
                <h4>Unique Award Titles</h4><h2>{unique_award_titles}</h2>
            </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
            <div class='glass-card' style='background-color:#90EE90; text-align:center;'>
                <h4>Top Team</h4><h2>{top_team}</h2>
            </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
            <div class='glass-card' style='background-color:#FFFACD; text-align:center;'>
                <h4>Most Common Award</h4><h2>{most_common_award}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # =============================
    # 🌈 1️⃣ Most Frequent Awards
    # =============================
    st.markdown("### 🏅 Most Frequently Given Awards")

    top_awards = df_filtered['New_Award_title'].value_counts().reset_index()
    top_awards.columns = ['Award Title', 'Count']

    fig1 = px.bar(
        top_awards,
        x='Award Title', y='Count', text='Count',
        color='Award Title',
        color_discrete_map=AWARD_COLORS,
        title="🏆 Most Frequently Given Awards"
    )
    fig1.update_traces(textfont_size=14, textposition='outside')
    fig1.update_layout(template='plotly_white', height=500)
    st.plotly_chart(fig1, use_container_width=True)

    # =============================
    # 👥 2️⃣ Team vs Award Type — Treemap
    # =============================
    st.markdown("### 👥 Team-Wise Award Distribution — Treemap View")

    team_awards = (
        df_filtered.groupby(['New_Award_title', 'Team name'])
        .size()
        .reset_index(name='Award Count')
    )
    team_awards = team_awards[~team_awards['Team name'].isin(['', 'Nan', '-', None])]

    fig2 = px.treemap(
        team_awards,
        path=['New_Award_title', 'Team name'],
        values='Award Count',
        color='New_Award_title',
        color_discrete_map=AWARD_COLORS,
        title="🏅 Award Distribution Across Teams & Award Types"
    )
    fig2.update_traces(textinfo="label+value+percent parent")
    st.plotly_chart(fig2, use_container_width=True)

    # =============================
    # 🔥 3️⃣ Top Award-Winning Teams
    # =============================
    st.markdown("### 🥇 Top Award-Winning Teams — Gradient View")

    leaderboard = (
        df_filtered.groupby('Team name')['New_Award_title']
        .count()
        .reset_index(name='Award Count')
        .sort_values(by='Award Count', ascending=False)
        .head(10)
    )

    fig3 = px.bar(
        leaderboard,
        x='Team name', y='Award Count',
        color='Award Count',
        color_continuous_scale='Sunsetdark',
        text='Award Count',
        title="🌟 Top 10 Teams by Total Awards"
    )
    fig3.update_traces(textposition='outside')
    fig3.update_layout(template='plotly_dark', height=550)
    st.plotly_chart(fig3, use_container_width=True)

    # =============================
    # 📈 4️⃣ Award Timeline Growth
    # =============================
    st.markdown("### ⏳ Award Growth Over Time — Animated Trend")

    timeline = (
        df_filtered.groupby(['Period', 'New_Award_title'])
        .size()
        .reset_index(name='Award Count')
    )

    fig_time = px.bar(
        timeline,
        x="New_Award_title",
        y="Award Count",
        animation_frame=timeline['Period'].dt.strftime('%b %Y'),
        color="New_Award_title",
        color_discrete_map=AWARD_COLORS,
        title="📈 Recognition Timeline by Award Type (Animated)",
    )
    fig_time.update_layout(template='plotly_white', height=600)

    st.plotly_chart(fig_time, use_container_width=True)


# Run standalone
if __name__ == "__main__":
    show_award_analysis()
