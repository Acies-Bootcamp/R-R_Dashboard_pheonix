import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# Award Color Palette
AWARD_COLORS = {
    "Team Award": "#A7C7E7",
    "Spot Award": "#F4C2C2",
    "Champion Award": "#90EE90",
    "Awesome Award": "#FFFACD",
    "OTA": "#FFCCCB",
}

ANALYSIS_AWARD_TYPES = [
    "Team Award",
    "Spot Award",
    "Champion Award",
    "Awesome Award",
]

def normalize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name

def map_sankey_bucket(title: str) -> str | None:
    if not isinstance(title, str):
        return None
    t = title.lower().strip()
    
    if "team" in t and "spot" not in t and "ota" not in t and "occasion" not in t:
        return "Team Award"
    if "spot" in t:
        return "Spot Award"
    if "ota" in t or "one time" in t or "one-time" in t:
        return "OTA"
    return None

@st.cache_data
def load_data():
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)
    
    df["Month"] = df["Month"].astype(str).str.strip().str.capitalize()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    df["Month_Num"] = df["Month"].map(month_map)
    df["Date"] = pd.to_datetime(
        dict(year=df["year"], month=df["Month_Num"], day=1),
        errors="coerce",
    )
    
    df["New_Award_title"] = df["New_Award_title"].astype(str).str.title().str.strip()
    df["Team name"] = df["Team name"].astype(str).str.title().str.strip()
    
    return df

def show_award_analysis():
    base_css = """
    <style>
    body {
        background-color: #f5f5f5;
        color: #222222;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .main > div {
        padding-top: 0.5rem;
    }
    h1, h2, h3, h4 {
        color: #222222 !important;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 18px;
        border: 1px solid #e3e3e3;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        text-align: center;
    }
    .metric-card h4 {
        font-size: 0.95rem;
        font-weight: 600;
        color: #666666;
        margin-bottom: 0.3rem;
    }
    .metric-card h2 {
        font-size: 1.6rem;
        font-weight: 700;
        color: #222222;
        margin: 0;
    }
    .section-title {
        font-weight: 600;
        font-size: 1.05rem;
        color: #333333;
        margin-bottom: 0.4rem;
    }
    .stPlotlyChart {
        background: radial-gradient(circle at top left,
                                    rgba(255,255,255,0.9),
                                    rgba(243,244,246,0.98));
        border-radius: 16px;
        padding: 12px;
        border: 1px solid rgba(209, 213, 219, 0.9);
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    }
    .kpi-label {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }
    .kpi-help {
        font-size: 0.75rem;
        color: #999999;
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
    </style>
    """
    st.markdown(base_css, unsafe_allow_html=True)

    df = load_data()
    
    st.markdown("<p class='section-title'>Filter Options</p>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            period = st.selectbox(
                "Select Period",
                ["Monthly", "Quarterly", "Yearly"],
                index=0,
            )
        
        with col2:
            years = sorted(df["year"].dropna().unique())
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
            award_type_options = ["All"] + ANALYSIS_AWARD_TYPES
            selected_award_types_raw = st.multiselect(
                "Award Type",
                options=award_type_options,
                default=["All"],
            )
            if "All" in selected_award_types_raw or not selected_award_types_raw:
                award_types = ANALYSIS_AWARD_TYPES
            else:
                award_types = selected_award_types_raw
        
        with col4:
            recognition_systems = sorted(df["Nominated In"].dropna().unique())
            rec_options = ["All"] + recognition_systems
            selected_sys = st.multiselect(
                "Recognition System", rec_options, default=["All"]
            )
        
        col5, col6 = st.columns(2)
        with col5:
            departments = sorted(df["Department"].dropna().unique())
            dept_options = ["All"] + departments
            selected_dept = st.multiselect(
                "Filter by Department", dept_options, default=["All"]
            )
        
        with col6:
            locations_raw = df["Seating Location"].dropna().unique()
            locations = sorted(
                set(x.replace("Bhive,", "Bhive, ") for x in locations_raw)
            )
            loc_options = ["All"] + locations
            selected_loc = st.multiselect(
                "Filter by Location", loc_options, default=["All"]
            )
    
    df_filtered = df[
        (df["year"].isin(selected_years))
        & (df["New_Award_title"].isin(award_types))
    ].copy()
    
    if "All" not in selected_sys:
        df_filtered = df_filtered[df_filtered["Nominated In"].isin(selected_sys)]
    
    if "All" not in selected_dept:
        df_filtered = df_filtered[df_filtered["Department"].isin(selected_dept)]
    
    if "All" not in selected_loc:
        df_filtered = df_filtered[df_filtered["Seating Location"].isin(selected_loc)]
    
    if period == "Monthly":
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("M").dt.to_timestamp()
    elif period == "Quarterly":
        df_filtered["Period"] = (
            df_filtered["Date"].dt.to_period("Q").dt.to_timestamp()
        )
    else:
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("Y").dt.to_timestamp()
    
    st.divider()
    
    if df_filtered.empty:
        st.info("No data available for the current filters.")
        return
    
    total_awards = len(df_filtered)
    old_title_count = df["Award Title"].nunique()
    new_title_count = len(ANALYSIS_AWARD_TYPES)
    
    team_awards_only = df_filtered[
        (df_filtered["New_Award_title"] == "Team Award")
        & (df_filtered["Team name"].notna())
        & (df_filtered["Team name"].str.strip() != "")
    ]
    if not team_awards_only.empty:
        top_team = team_awards_only["Team name"].value_counts().idxmax()
    else:
        top_team = "—"
    
    most_common_award = (
        df_filtered["New_Award_title"].value_counts().idxmax()
        if not df_filtered.empty
        else "—"
    )
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(
            f"""
            <div class='metric-card'>
                <h4>
                  <span class="kpi-label">
                    Total Awards
                    <span class="kpi-help" title="Count of all awards across the four main consolidated award types in the selected period and filters.">?</span>
                  </span>
                </h4>
                <h2>{total_awards}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            f"""
            <div class='metric-card'>
                <h4>
                  <span class="kpi-label">
                    Award Titles (Old → New)
                    <span class="kpi-help" title="Number of raw award titles historically used vs the four simplified categories used in the new system.">?</span>
                  </span>
                </h4>
                <h2>{old_title_count} → {new_title_count}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi3:
        st.markdown(
            f"""
            <div class='metric-card'>
                <h4>
                  <span class="kpi-label">
                    Most Recognized Team
                    <span class="kpi-help" title="Team that has received the highest number of Team Awards under the current filters.">?</span>
                  </span>
                </h4>
                <h2>{top_team}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi4:
        st.markdown(
            f"""
            <div class='metric-card'>
                <h4>
                  <span class="kpi-label">
                    Most Common Award Type
                    <span class="kpi-help" title="The most frequently used award category (Team / Spot / Champion / Awesome) in the filtered data.">?</span>
                  </span>
                </h4>
                <h2>{most_common_award}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.divider()
    
    st.markdown(
        "<p class='section-title'>Award Title Mapping (Sankey)</p>",
        unsafe_allow_html=True,
    )
    
    df_for_sankey = df.copy()
    df_for_sankey = df_for_sankey[df_for_sankey["year"].isin(selected_years)]
    
    if "All" not in selected_sys:
        df_for_sankey = df_for_sankey[
            df_for_sankey["Nominated In"].isin(selected_sys)
        ]
    if "All" not in selected_dept:
        df_for_sankey = df_for_sankey[
            df_for_sankey["Department"].isin(selected_dept)
        ]
    if "All" not in selected_loc:
        df_for_sankey = df_for_sankey[
            df_for_sankey["Seating Location"].isin(selected_loc)
        ]
    
    df_for_sankey["Sankey_Target"] = df_for_sankey["New_Award_title"].apply(
        map_sankey_bucket
    )
    df_for_sankey = df_for_sankey.dropna(subset=["Sankey_Target"])
    
    sankey_targets = sorted(df_for_sankey["Sankey_Target"].unique())
    
    if not sankey_targets:
        st.info("No Sankey targets (Team / Spot / OTA) in current filters.")
    else:
        tabs = st.tabs(sankey_targets)
        
        for tab, target_award in zip(tabs, sankey_targets):
            with tab:
                sankey_df = df_for_sankey[
                    df_for_sankey["Sankey_Target"] == target_award
                ]
                if sankey_df.empty:
                    st.info("No data available for this bucket in the current filters.")
                    continue
                
                sankey_group = (
                    sankey_df.groupby(["Award Title", "Sankey_Target"])
                    .size()
                    .reset_index(name="Count")
                )
                
                raw_titles = (
                    sankey_group["Award Title"].astype(str).unique().tolist()
                )
                labels = raw_titles + [target_award]
                label_to_idx = {lbl: i for i, lbl in enumerate(labels)}
                
                sources = [
                    label_to_idx[row["Award Title"]]
                    for _, row in sankey_group.iterrows()
                ]
                targets = [
                    label_to_idx[target_award] for _ in sankey_group.itertuples()
                ]
                values = sankey_group["Count"].tolist()
                
                link_color = AWARD_COLORS.get(target_award, "#A7C7E7")
                
                fig_sankey = go.Figure(
                    data=[
                        go.Sankey(
                            node=dict(
                                pad=18,
                                thickness=18,
                                line=dict(color="black", width=0.4),
                                label=labels,
                                color=["#e0e0e0"] * len(raw_titles) + [link_color],
                            ),
                            link=dict(
                                source=sources,
                                target=targets,
                                value=values,
                                color=[link_color] * len(values),
                            ),
                        )
                    ]
                )
                
                fig_sankey.update_layout(
                    title=f"Raw Award Titles → {target_award}",
                    font=dict(size=14, color="black"),
                    height=520,
                    margin=dict(l=10, r=10, t=40, b=10),
                    template="plotly_white",
                )
                st.plotly_chart(fig_sankey, use_container_width=True)
    
    st.divider()
    
    st.markdown(
        "<p class='section-title'>Most Frequently Given Awards</p>",
        unsafe_allow_html=True,
    )
    
    top_awards = df_filtered["New_Award_title"].value_counts().reset_index()
    top_awards.columns = ["Award Title", "Count"]
    
    fig1 = px.bar(
        top_awards,
        x="Award Title",
        y="Count",
        text="Count",
        color="Award Title",
        color_discrete_map=AWARD_COLORS,
        title="Most Frequently Given Awards",
    )
    fig1.update_traces(textfont_size=14, textposition="outside")
    fig1.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown(
        "<p class='section-title'>Team-Wise Award Distribution (Treemap)</p>",
        unsafe_allow_html=True,
    )
    
    team_awards = (
        df_filtered.groupby(["New_Award_title", "Team name"])
        .size()
        .reset_index(name="Award Count")
    )
    team_awards = team_awards[
        ~team_awards["Team name"].isin(["", "Nan", "-", None])
    ]
    
    if not team_awards.empty:
        fig2 = px.treemap(
            team_awards,
            path=["New_Award_title", "Team name"],
            values="Award Count",
            color="New_Award_title",
            color_discrete_map=AWARD_COLORS,
            title="Award Distribution Across Teams and Award Types",
        )
        fig2.update_traces(textinfo="label+value+percent parent")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data for the treemap with current filters.")
    
    st.markdown(
        "<p class='section-title'>Top Award-Winning Teams</p>",
        unsafe_allow_html=True,
    )
    
    leaderboard = (
        df_filtered.groupby("Team name")["New_Award_title"]
        .count()
        .reset_index(name="Award Count")
        .sort_values(by="Award Count", ascending=False)
        .head(10)
    )
    
    if not leaderboard.empty:
        fig3 = px.bar(
            leaderboard,
            x="Team name",
            y="Award Count",
            color="Award Count",
            color_continuous_scale="Sunsetdark",
            text="Award Count",
            title="Top 10 Teams by Total Awards",
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(template="plotly_dark", height=550)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No team data available for the current filters.")
    
    st.markdown(
        "<p class='section-title'>Award Growth Over Time</p>",
        unsafe_allow_html=True,
    )
    
    timeline = (
        df_filtered.groupby(["Period", "New_Award_title"])
        .size()
        .reset_index(name="Award Count")
    )
    
    if timeline.empty:
        st.info("No timeline data available for the current filters.")
    else:
        fig_time = px.line(
            timeline,
            x="Period",
            y="Award Count",
            color="New_Award_title",
            markers=True,
            color_discrete_map=AWARD_COLORS,
            title="Recognition Timeline by Award Type",
        )
        fig_time.update_layout(template="plotly_white", height=500)
        st.plotly_chart(fig_time, use_container_width=True)

if __name__ == "__main__":
    show_award_analysis()
