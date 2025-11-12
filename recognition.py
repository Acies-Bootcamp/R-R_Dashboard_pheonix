import streamlit as st
import pandas as pd
import plotly.express as px
import re

def normalize_name(name):
    if pd.isna(name): return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name

def load_and_process_data():
    url = "https://docs.google.com/spreadsheets/d/1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q/export?format=xlsx"
    df = pd.read_excel(url)

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['Month'] = df['Month'].astype(str).str.strip().str.capitalize()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['Month_Num'] = df['Month'].map(month_map)
    df['Date'] = pd.to_datetime(dict(year=df['year'], month=df['Month_Num'], day=1), errors='coerce')

    # Normalize teams for all
    team_mapping = {
        'greenmath': 'Greenmath', 'edgecore': 'Edgecore',
        'edgecre': 'Edgecore', 'pr - greenmath launch': 'PR - Greenmath Launch',
        # Add more mapping if needed
    }
    df['Team name'] = df['Team name'].str.lower().map(lambda t: team_mapping.get(t, t)).str.title()
    return df

def show_recognition_team_tab():
    df = load_and_process_data()
    st.title("Awards Trends: Team & Awesome Awards")

    col1, col2, col3, col4 = st.columns([2,2,2,2])
    with col1:
        period_options = ["Monthly", "Quarterly", "Yearly"]
        time_period = st.selectbox("Select Period", period_options, index=0)
    with col2:
        years = sorted(df['year'].dropna().unique())
        selected_years = st.multiselect("Year(s)", years, default=years[-2:])
    with col3:
        mode = st.selectbox("Team Display Mode", ["All Teams", "Top Teams", "Single Team"], index=1)
    with col4:
        teams = sorted(df['Team name'].dropna().unique())
        top_team_count = st.slider("No. Top Teams", min_value=5, max_value=min(20,len(teams)), value=10) if mode=="Top Teams" else None
        selected_team = st.selectbox("Select Team", ["All Teams"] + teams) if mode=="Single Team" else None

    # --- Team Award Filter ---
    team_award_df = df[df['New_Award_title'] == 'Team Award']
    # Team selection logic
    if mode == "All Teams":
        active_teams = teams
    elif mode == "Single Team":
        active_teams = teams if selected_team=="All Teams" else [selected_team]
    elif mode == "Top Teams":
        top_teams = team_award_df.groupby('Team name').size().sort_values(ascending=False).head(top_team_count).index.tolist()
        active_teams = top_teams

    filtered_team_award = team_award_df[
        (team_award_df['year'].isin(selected_years)) &
        (team_award_df['Team name'].isin(active_teams))
    ]
    # Period aggregation
    if time_period == "Monthly":
        filtered_team_award['Period'] = filtered_team_award['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        filtered_team_award['Period'] = filtered_team_award['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        filtered_team_award['Period'] = filtered_team_award['Date'].dt.to_period('Y').dt.to_timestamp()
    trend_df = filtered_team_award.groupby(['Period', 'Team name']).size().reset_index(name='Count')
    fig = px.line(trend_df, x='Period', y='Count', color='Team name', symbol='Team name',
                  markers=True, title="Team Award Trends Over Time")
    fig.update_layout(xaxis_title="Month - Year", yaxis_title="No. of Team Awards")
    st.plotly_chart(fig, use_container_width=True)

    # --- Awesome Award Greenmath/Edgecore Line ---
    awesome_awards_df = df[df['New_Award_title'] == 'Awesome Award']
    awesome_awards_df = awesome_awards_df[
        (awesome_awards_df['Team name'].isin(['Greenmath', 'Edgecore'])) &
        (awesome_awards_df['year'].isin(selected_years))
    ]
    awesome_awards_trend = (
        awesome_awards_df.groupby(['Team name', 'Date'], as_index=False)
        .size()
        .rename(columns={'size': 'Award_Count'})
        .sort_values('Date')
    )
    fig2 = px.line(
        awesome_awards_trend, x='Date', y='Award_Count', color='Team name',
        markers=True, title='Awesome Award Trends for Greenmath and Edgecore',
        color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
    )
    fig2.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=45)
    fig2.update_layout(
        xaxis_title='Month – Year',
        yaxis_title='No. of Awesome Awards',
        hovermode='x unified',
        template='plotly_white'
    )
    st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    show_recognition_team_tab()
