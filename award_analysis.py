import streamlit as st
import styles
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

<<<<<<< HEAD
=======
# ===================== TEAM NORMALIZATION =====================
TEAM_NORMALIZATION = {
    "edgecore": "Edgecore",
    "edge core": "Edgecore",
    "greenmath": "Greenmath",
    "greenmath team": "Greenmath",
    "greenmath launch": "Greenmath Launch",
    "greenmath  launch": "Greenmath Launch",
    # add more variants here if you spot any in the raw data
}

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

def normalize_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z\s]", "", name)
    return name


<<<<<<< HEAD
=======
def canonical_team(name: str) -> str:
    """
    Normalize and map raw team names into canonical labels.
    """
    if not isinstance(name, str):
        return ""
    norm = normalize_name(name)
    if norm in TEAM_NORMALIZATION:
        return TEAM_NORMALIZATION[norm]
    # fallback: cleaned title-case original
    return name.strip().title()


def is_unknown_team(name) -> bool:
    """
    Return True if the team name is empty / NaN / or some 'Unknown...' placeholder.
    These rows will be excluded from team-based charts.
    """
    if pd.isna(name):
        return True

    s = str(name).strip().lower()
    if not s:
        return True

    # simple exact placeholders
    if s in {"nan", "none", "-", "unknown", "unknown team", "unknown team name", "unassigned"}:
        return True

    # normalise non-letters to spaces and look for 'unknown' token
    s_clean = re.sub(r"[^a-z]", " ", s)
    tokens = s_clean.split()

    # e.g. "unknown team name_aw", "unknown team name aw", etc.
    if "unknown" in tokens:
        return True

    # extra safety: any string that starts with "unknown"
    if s.startswith("unknown"):
        return True

    return False


>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
def map_sankey_bucket(title: str) -> str | None:
    if not isinstance(title, str):
        return None
    t = title.lower().strip()
<<<<<<< HEAD
=======

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    if "team" in t and "spot" not in t and "ota" not in t and "occasion" not in t:
        return "Team Award"
    if "spot" in t:
        return "Spot Award"
    if "ota" in t or "one time" in t or "one-time" in t:
        return "OTA"
    return None


@st.cache_data
def load_data():
    # Replace sheet_key with your own key if needed
    sheet_key = "1xVpXomZBOyIeyvpyDjXQlSEIfU35v6j0jkhdaETm4-Q"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    df = pd.read_csv(url)

<<<<<<< HEAD
    # Normalize Month & Year and create Date
    df["Month"] = df.get("Month", "").astype(str).str.strip().str.capitalize()
    # Convert year to numeric; store as nullable Int64
    df["year"] = pd.to_numeric(df.get("year", None), errors="coerce").astype("Int64")
=======
    df["Month"] = df["Month"].astype(str).str.strip().str.capitalize()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    df["Month_Num"] = df["Month"].map(month_map)
    # build Date; day=1
    df["Date"] = pd.to_datetime(
        dict(year=df["year"].astype("Int64"), month=df["Month_Num"], day=1),
        errors="coerce",
    )

<<<<<<< HEAD
    # Clean award/title/team strings consistently
    df["New_Award_title"] = df.get("New_Award_title", "").astype(str).str.title().str.strip()
    df["Team name"] = df.get("Team name", "").astype(str).str.title().str.strip()
    df["Award Title"] = df.get("Award Title", "").astype(str).str.strip()
    df["Nominated In"] = df.get("Nominated In", "").astype(str).str.strip()
    df["Department"] = df.get("Department", "").astype(str).str.strip()
    df["Seating Location"] = df.get("Seating Location", "").astype(str).str.strip()
=======
    df["New_Award_title"] = df["New_Award_title"].astype(str).str.title().str.strip()

    # canonicalise team names
    df["Team name"] = df["Team name"].astype(str).apply(canonical_team)
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

    return df


def show_award_analysis():
    """
    Render the award analysis dashboard.
    """
    theme = st.session_state.get("theme", "White")
    styles.apply_styles(theme=theme)

    df = load_data()

    st.markdown("<p class='section-title'>Filter Options</p>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3, col4 = st.columns(4)

        # Period selector
        with col1:
            period = st.selectbox(
                "Select Period",
                ["Monthly", "Quarterly", "Yearly"],
                index=0,
            )

<<<<<<< HEAD
        # Year selector (fixed and robust)
        with col2:
            # get numeric years as plain ints (dropna)
            years = sorted(df["year"].dropna().astype(int).unique().tolist())
            year_options = ["All"] + years
=======
        # Year selector
        with col2:
            years = sorted(df["year"].dropna().astype(int).unique())
            year_options = ["All"] + list(years)
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

            selected_years_raw = st.multiselect(
                "Select Year(s)",
                options=year_options,
                default=["All"],
            )

<<<<<<< HEAD
            # Normalized selected_years as list[int]
            if "All" in selected_years_raw or not selected_years_raw:
                selected_years = years[:]  # all numeric years
            else:
                # Convert any numeric-like picks to ints (ignore anything else)
                # Selected items will be ints because options included ints
                selected_years = [int(y) for y in selected_years_raw if isinstance(y, (int, float,))]

        # Award type selector
=======
            if "All" in selected_years_raw or not selected_years_raw:
                selected_years = list(years)
            else:
                selected_years = [int(y) for y in selected_years_raw if y != "All"]

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        with col3:
            award_type_options = ["All"] + ANALYSIS_AWARD_TYPES
            selected_award_types_raw = st.multiselect(
                "Award Type",
                options=award_type_options,
                default=["All"],
            )
            if "All" in selected_award_types_raw or not selected_award_types_raw:
                award_types = ANALYSIS_AWARD_TYPES[:]
            else:
<<<<<<< HEAD
                # Keep values as-is (strings)
                award_types = [a for a in selected_award_types_raw if isinstance(a, str)]

        # Recognition systems
=======
                award_types = selected_award_types_raw

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        with col4:
            recognition_systems = sorted([s for s in df["Nominated In"].dropna().unique().tolist() if str(s).strip() != ""])
            rec_options = ["All"] + recognition_systems
            selected_sys = st.multiselect(
                "Recognition System", rec_options, default=["All"]
            )

<<<<<<< HEAD
        # Departments & Locations (second row)
=======
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        col5, col6 = st.columns(2)
        with col5:
            departments = sorted([d for d in df["Department"].dropna().unique().tolist() if str(d).strip() != ""])
            dept_options = ["All"] + departments
            selected_dept = st.multiselect(
                "Filter by Department", dept_options, default=["All"]
            )

        with col6:
            locations_raw = df["Seating Location"].dropna().unique().tolist()
            # quick normalization on Bhive case and blank-like values
            locations = sorted(
                [x.replace("Bhive,", "Bhive, ").strip() for x in locations_raw if str(x).strip() != ""]
            )
            loc_options = ["All"] + locations
            selected_loc = st.multiselect(
                "Filter by Location", loc_options, default=["All"]
            )

<<<<<<< HEAD
    # Build filtered dataframe safely
    # Ensure year-based filtering uses numeric year
    df_filtered = df.copy()

    # Year filter
    if selected_years:
        # Ensure we only filter by year if df has year values
        df_filtered = df_filtered[df_filtered["year"].notna()]
        df_filtered = df_filtered[df_filtered["year"].astype(int).isin(selected_years)]

    # Award type filter
    if award_types:
        df_filtered = df_filtered[df_filtered["New_Award_title"].isin(award_types)]

    # Recognition System filter
    if selected_sys and "All" not in selected_sys:
        df_filtered = df_filtered[df_filtered["Nominated In"].isin(selected_sys)]

    # Department filter
    if selected_dept and "All" not in selected_dept:
        df_filtered = df_filtered[df_filtered["Department"].isin(selected_dept)]

    # Location filter
    if selected_loc and "All" not in selected_loc:
        df_filtered = df_filtered[df_filtered["Seating Location"].isin(selected_loc)]

    # Period column creation depending on period selection
=======
    # ========= APPLY FILTERS =========
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

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    if period == "Monthly":
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("M").dt.to_timestamp()
    elif period == "Quarterly":
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("Q").dt.to_timestamp()
    else:
        df_filtered["Period"] = df_filtered["Date"].dt.to_period("Y").dt.to_timestamp()

    st.divider()

    if df_filtered.empty:
        st.info("No data available for the current filters.")
        return

<<<<<<< HEAD
    # KPIs
=======
    # ========= KPIs =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    total_awards = len(df_filtered)
    old_title_count = df[df["Nominated In"].str.lower() == "all-hands"]["Award Title"].nunique()
    new_title_count = len(ANALYSIS_AWARD_TYPES)

<<<<<<< HEAD
=======
    # Top team (exclude unknowns)
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    team_awards_only = df_filtered[
        (df_filtered["New_Award_title"] == "Team Award")
        & (~df_filtered["Team name"].apply(is_unknown_team))
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
                    <span class="kpi-help" title="Team that has received the highest number of Team Awards under the current filters (after grouping variants like Edgecore / Greenmath / Greenmath Launch).">?</span>
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

<<<<<<< HEAD
    # Sankey mapping visualization
=======
    # ========= SANKEY =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    st.markdown(
        "<p class='section-title'>Award Title Mapping (Sankey)</p>",
        unsafe_allow_html=True,
    )

    df_for_sankey = df.copy()
<<<<<<< HEAD
    # Apply similar filter criteria to Sankey except award mapping is from raw Award Title -> Sankey_Target
    # Year filter for sankey
    if selected_years:
        df_for_sankey = df_for_sankey[df_for_sankey["year"].notna()]
        df_for_sankey = df_for_sankey[df_for_sankey["year"].astype(int).isin(selected_years)]
    if selected_sys and "All" not in selected_sys:
        df_for_sankey = df_for_sankey[df_for_sankey["Nominated In"].isin(selected_sys)]
    if selected_dept and "All" not in selected_dept:
        df_for_sankey = df_for_sankey[df_for_sankey["Department"].isin(selected_dept)]
    if selected_loc and "All" not in selected_loc:
        df_for_sankey = df_for_sankey[df_for_sankey["Seating Location"].isin(selected_loc)]

    df_for_sankey["Sankey_Target"] = df_for_sankey["New_Award_title"].apply(map_sankey_bucket)
=======
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
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    df_for_sankey = df_for_sankey.dropna(subset=["Sankey_Target"])

    sankey_targets = sorted(df_for_sankey["Sankey_Target"].unique())

<<<<<<< HEAD
=======
    def clean_team_list(series):
        unique = {t.strip() for t in series.astype(str)}
        unique = {t for t in unique if not is_unknown_team(t)}
        return ", ".join(sorted(unique)) if unique else "No team info"

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    if not sankey_targets:
        st.info("No Sankey targets (Team / Spot / OTA) in current filters.")
    else:
        tabs = st.tabs(sankey_targets)

        for tab, target_award in zip(tabs, sankey_targets):
            with tab:
                sankey_df = df_for_sankey[df_for_sankey["Sankey_Target"] == target_award]
                if sankey_df.empty:
                    st.info("No data available for this bucket in the current filters.")
                    continue

                sankey_group = (
                    sankey_df.groupby(["Award Title", "Sankey_Target"])
                    .size()
                    .reset_index(name="Count")
                )

<<<<<<< HEAD
=======
                team_names_by_title = (
                    sankey_df.dropna(subset=["Award Title", "Team name"])
                    .groupby("Award Title")["Team name"]
                    .apply(clean_team_list)
                    .to_dict()
                )

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
                raw_titles = sankey_group["Award Title"].astype(str).unique().tolist()
                labels = raw_titles + [target_award]
                label_to_idx = {lbl: i for i, lbl in enumerate(labels)}

<<<<<<< HEAD
                sources = [label_to_idx[row["Award Title"]] for _, row in sankey_group.iterrows()]
                targets = [label_to_idx[target_award] for _ in sankey_group.itertuples()]
                values = sankey_group["Count"].tolist()

=======
                sources = [
                    label_to_idx[row["Award Title"]]
                    for _, row in sankey_group.iterrows()
                ]
                targets = [
                    label_to_idx[target_award] for _ in sankey_group.itertuples()
                ]
                values = sankey_group["Count"].tolist()

                link_customdata = [
                    team_names_by_title.get(row["Award Title"], "No team info")
                    for _, row in sankey_group.iterrows()
                ]

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
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
                                customdata=link_customdata,
                                hovertemplate="Teams: %{customdata}<extra></extra>",
                            ),
                        )
                    ]
                )

                fig_sankey.update_layout(
                    title=f"Raw Award Titles → {target_award}",
                    font=dict(size=15, color="black"),
                    height=620,
                    margin=dict(l=10, r=10, t=50, b=20),
                    template="plotly_white",
                )
                st.plotly_chart(fig_sankey, use_container_width=True)

    st.divider()

<<<<<<< HEAD
    # Most frequently given awards (bar)
=======
    # ========= MOST FREQUENT AWARDS =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
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

<<<<<<< HEAD
    # Team-wise treemap
=======
    # ========= TEAM TREEMAP =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    st.markdown(
        "<p class='section-title'>Team-Wise Award Distribution (Treemap)</p>",
        unsafe_allow_html=True,
    )

    team_awards = (
        df_filtered.groupby(["New_Award_title", "Team name"])
        .size()
        .reset_index(name="Award Count")
    )
<<<<<<< HEAD
    team_awards = team_awards[~team_awards["Team name"].isin(["", "Nan", "-", None])]
=======
    team_awards = team_awards[~team_awards["Team name"].apply(is_unknown_team)]
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

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

<<<<<<< HEAD
    # Leaderboard
=======
    # ========= TOP TEAMS LEADERBOARD =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    st.markdown(
        "<p class='section-title'>Top Award-Winning Teams</p>",
        unsafe_allow_html=True,
    )

<<<<<<< HEAD
=======
    df_leader = df_filtered[~df_filtered["Team name"].apply(is_unknown_team)].copy()

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    leaderboard = (
        df_leader.groupby("Team name")
        .agg(
            People_Count=("Employee Name", "nunique"),
            Award_Count=("New_Award_title", "count"),
        )
        .reset_index()
    )

<<<<<<< HEAD
=======
    leaderboard["Recognition_Score"] = (
        (leaderboard["People_Count"] * 0.6)
        + (leaderboard["Award_Count"] * 0.4)
    ).round(2)

    leaderboard = leaderboard.sort_values(
        by="Recognition_Score", ascending=False
    ).head(10)

>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
    if not leaderboard.empty:
        fig3 = px.bar(
            leaderboard,
            x="Team name",
            y="Recognition_Score",
            color="Team name",
            text="Recognition_Score",
            title="Top 10 Teams by Recognition Score (People + Awards)",
            hover_data={
                "People_Count": True,
                "Award_Count": True,
                "Recognition_Score": True,
            },
        )
        fig3.update_traces(
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Recognition Score: %{y:.2f}<br>"
                "People: %{customdata[0]}<br>"
                "Awards: %{customdata[1]}"
                "<extra></extra>"
            ),
        )
        fig3.update_layout(
            template="plotly_white",
            height=480,
            margin=dict(l=40, r=30, t=60, b=40),
            xaxis_title="Team",
            yaxis_title="Recognition Score",
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.caption(
            "**Recognition Score** = (People Count × 0.6) + (Award Count × 0.4) — "
            "This balanced metric considers both team size and total awards received."
        )
    else:
        st.info("No team data available for the current filters.")

<<<<<<< HEAD
    # Timeline
=======
    # ========= AWARD GROWTH OVER TIME =========
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
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

        fig_time.update_traces(
            mode="lines+markers",
            line=dict(width=3.5, color=None),
            marker=dict(size=10, line=dict(width=1, color="black")),
        )

        fig_time.update_layout(
            template="plotly_white",
            height=480,
            hovermode="x unified",
            margin=dict(l=30, r=30, t=50, b=40),
            legend_title_text="Award Type",
        )

        fig_time.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
        fig_time.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.1)")

        st.plotly_chart(fig_time, use_container_width=True)


if __name__ == "__main__":
    show_award_analysis()
