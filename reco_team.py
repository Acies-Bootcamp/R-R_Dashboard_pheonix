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
    
    # Normalize team names for consistency
    team_mapping = {
        'greenmath': 'Greenmath',
        'edgecore': 'Edgecore',
        'edgecre': 'Edgecore',
        'pr - greenmath launch': 'PR - Greenmath Launch',
        # Add more mapping if needed
    }
    df['Team name'] = df['Team name'].str.lower().map(lambda t: team_mapping.get(t, t)).str.title()

    return df

def build_award_trend(df, award_types, selected_years, time_period, team_mode, selected_team, top_team_count, kudos_corner=False):
    dfs = []

    # Filter by Kudos Corner if selected
    if kudos_corner:
        df = df[df['Nominated'] == "Kudos Corner"]

    # TEAM AWARD
    if "Team Award" in award_types:
        team_award_df = df[df['New_Award_title'] == 'Team Award']
        teams = sorted(team_award_df['Team name'].dropna().unique())

        if team_mode == "All Teams":
            active_teams = teams
        elif team_mode == "Single Team":
            active_teams = [selected_team] if selected_team != "All Teams" else teams
        elif team_mode == "Top Teams":
            top_teams = team_award_df['Team name'].value_counts().head(top_team_count).index.tolist()
            active_teams = top_teams

        filtered = team_award_df[
            (team_award_df['year'].isin(selected_years)) &
            (team_award_df['Team name'].isin(active_teams))
        ].copy()
        filtered['Award_Type'] = 'Team Award'

        dfs.append(filtered)

    # AWESOME AWARD (for product teams like Greenmath and Edgecore)
    if "Awesome Award" in award_types:
        # Filter employees belonging to these teams
        greenmath_employees = df[df['Team name'].str.contains('green', case=False, na=False)]
        edgecore_employees = df[df['Team name'].str.contains('edgecore', case=False, na=False)]
        filtered_employees = pd.concat([greenmath_employees, edgecore_employees])
        filtered_employees = filtered_employees[['Employee Name', 'Team name']]

        awesome_awards_raw = df[df['New_Award_title'] == 'Awesome Award'].copy()
        mapped_awards_df = awesome_awards_raw.merge(filtered_employees, on='Employee Name', how='left')
        mapped_awards_df = mapped_awards_df[
            mapped_awards_df['Team name_y'].str.contains('green|edgecore', case=False, na=False) &
            mapped_awards_df['year'].isin(selected_years)
        ].copy()
        mapped_awards_df = mapped_awards_df.rename(columns={'Team name_y': 'Team name'})
        mapped_awards_df['Award_Type'] = 'Awesome Award'

        dfs.append(mapped_awards_df)

    if not dfs:
        return None, None

    combined_df = pd.concat(dfs)

    if time_period == "Monthly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('M').dt.to_timestamp()
    elif time_period == "Quarterly":
        combined_df['Period'] = combined_df['Date'].dt.to_period('Q').dt.to_timestamp()
    else:
        combined_df['Period'] = combined_df['Date'].dt.to_period('Y').dt.to_timestamp()

    trend_df = combined_df.groupby(['Period', 'Team name', 'Award_Type']).size().reset_index(name='Award_Count')
    return trend_df, combined_df


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
            selected_years = st.multiselect("Year(s)", years, default=years)
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
            top_team_count = st.slider("No. Top Teams", min_value=5, max_value=min(20, len(teams)), value=10) if team_mode == "Top Teams" else None
        with col6:
            kudos_filter = st.checkbox("Kudos Corner", value=False)

        selected_team = st.selectbox("Select Team", ["All Teams"] + teams) if team_mode == "Single Team" else None

    trend_df, _ = build_award_trend(df, award_types, selected_years, time_period, team_mode, selected_team, top_team_count, kudos_corner=kudos_filter)
    if trend_df is None or trend_df.empty:
        st.warning("No data for selected filters.")
        return

    fig = px.line(
        trend_df, x='Period', y='Award_Count',
        color='Team name', symbol='Award_Type',
        markers=True,
        title="Award Trends Over Time",
        line_dash='Award_Type',
        color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
    )
    if time_period == "Monthly":
        fig.update_xaxes(
            dtick="M1",
            tickformat="%b %Y",
            tickangle=45,
            tickvals=trend_df['Period'].drop_duplicates()
        )
    elif time_period == "Quarterly":
        fig.update_xaxes(
            dtick="Q1",
            tickformat="Q%q %Y",
            tickangle=45,
            tickvals=trend_df['Period'].drop_duplicates()
        )
    elif time_period == "Yearly":
        fig.update_xaxes(
            dtick="Y1",
            tickformat="%Y",
            tickangle=45,
            tickvals=trend_df['Period'].drop_duplicates()
        )
    fig.update_layout(
        xaxis_title='Time Period',
        yaxis_title='Number of Awards',
        hovermode='x unified',
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)



def show_recognition_team_tab():
    df = load_and_process_data()
    st.title("Team & Awesome Awards Trends")

    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        with col1:
            period_options = ["Monthly", "Quarterly", "Yearly"]
            time_period = st.selectbox("Select Period", period_options, index=0)
        with col2:
            years = sorted(df['year'].dropna().unique())
            selected_years = st.multiselect("Year(s)", years, default=years[-2:])
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
            top_team_count = st.slider("No. Top Teams", min_value=5, max_value=min(20, len(teams)), value=10) if team_mode == "Top Teams" else None
            selected_team = st.selectbox("Select Team", ["All Teams"] + teams) if team_mode == "Single Team" else None

    trend_df, _ = build_award_trend(df, award_types, selected_years, time_period, team_mode, selected_team, top_team_count)
    if trend_df is None or trend_df.empty:
        st.warning("No data for selected filters.")
    else:
        fig = px.line(
            trend_df, x='Period', y='Award_Count',
            color='Team name', symbol='Award_Type',
            markers=True,
            title="Award Trends Over Time",
            line_dash='Award_Type',
            color_discrete_map={"Greenmath": "#bcbd22", "Edgecore": "#8c564b"}
        )
        
        # Adjust x-axis formatting based on selected period
        if time_period == "Monthly":
            fig.update_xaxes(
                dtick="M1",  # Monthly ticks
                tickformat="%b %Y",  # Display Month and Year
                tickangle=45,
                tickvals=trend_df['Period'].drop_duplicates()
            )
        elif time_period == "Quarterly":
            fig.update_xaxes(
                dtick="Q1",  # Quarterly ticks
                tickformat="Q%q %Y",  # Display Quarter (Q1, Q2, etc.) and Year
                tickangle=45,
                tickvals=trend_df['Period'].drop_duplicates()
            )
        elif time_period == "Yearly":
            # For Yearly, we only show the years
            fig.update_xaxes(
                dtick="Y1",  # Yearly ticks
                tickformat="%Y",  # Display Year only
                tickangle=45,
                tickvals=trend_df['Period'].drop_duplicates()
            )
        
        fig.update_layout(
            xaxis_title='Time Period',
            yaxis_title='Number of Awards',
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_recognition_team_tab()
