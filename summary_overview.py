import os
import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from collections import Counter

try:
    import google.generativeai as genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

_WORDCLOUD_OK = True
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
except Exception:
    _WORDCLOUD_OK = False


# ================= GLASS / MONOCHROME UI =================
glass_css = """
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

/* Metric card like other dashboards */
.metric-card {
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(15,23,42,0.08);
  border: 1px solid #e5e7eb;
  padding: 20px 18px 14px 18px;
  margin-bottom: 20px;
  text-align:center;
}
.metric-card h4 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 0.4rem;
}
.metric-card h2 {
    font-size: 1.7rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
}

/* KPI label + ? icon */
.kpi-label {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
}
.kpi-help {
    font-size: 0.75rem;
    color: #9ca3af;
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

/* Glass-style wrapper for all Plotly charts */
.stPlotlyChart {
    background: radial-gradient(circle at top left,
                                rgba(255,255,255,0.96),
                                rgba(243,244,246,1));
    border-radius: 16px;
    padding: 12px;
    border: 1px solid rgba(209, 213, 219, 0.9);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
}

/* Section titles */
.section-title {
    font-weight: 600;
    font-size: 1.05rem;
    color: #374151;
    margin-bottom: 0.4rem;
}
</style>
"""
st.markdown(glass_css, unsafe_allow_html=True)


# ================= COLUMN KEYS =================
COLS = {
    "timestamp": "Timestamp",
    "team": "Team Name ",
    "aware_earlier": "Are you aware of the earlier R&R system?",
    "earlier_rating": "How would you rate your overall experience with the earlier R&R system?",
    "earlier_like": "What did you like most about the earlier R&R system?",
    "engaging": "Which version of the R&R program do you find more engaging?",
    "kudos_special": "Did seeing awards in kudos corner feel as special as hearing them announced in All Hands?",
    "comments_earlier": "Any other comments about the earlier R&R system?",
    "have_current": "Have you ever received or given an award in the current Kudos Bot system?",
    "like_current": "What do you like most about the current R&R system?",
    "which_awards": "Which award(s) have you received?",
    "improve_current": "What improvements would you like to see in the current R&R system?",
    "comments_any": "Any additional comments or suggestions?"
}


# ================= LOAD SURVEY =================
@st.cache_data
def load_survey_data():
    sheet_key = "1KSuP5YlzyI1jdVTMMu5v7MLyzvP9Emr3Fo94BsiSFo0"
    df = pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv",
        on_bad_lines="skip",
        encoding="utf-8"
    )
    df.columns = df.columns.str.strip().str.replace("\n", " ").str.replace("\r", "")
    return df


def clean_text(x):
    return "" if pd.isna(x) else str(x).strip()


def parse_awards(cell):
    text = clean_text(cell)
    if not text:
        return []
    parts = re.split(r"[,/|;]", text)
    return [
        p.strip()
        for p in parts
        if p.strip().lower() not in {"na", "none", "no award", "no award yet", "-", ""}
    ]


def earlier_rating_score(df):
    s = pd.to_numeric(df[COLS["earlier_rating"]], errors="coerce")
    return float((s.mean() / 3) * 100) if not s.dropna().empty else np.nan


def score_sentiment_texts(texts):
    texts = [clean_text(t) for t in texts if clean_text(t)]
    if not texts:
        return np.nan
    sia = SentimentIntensityAnalyzer()
    vals = [(sia.polarity_scores(t)["compound"] + 1) / 2 * 100 for t in texts]
    return float(np.mean(vals))


def current_sentiment_score(df):
    fields = ["like_current", "improve_current", "comments_any"]
    texts = []
    for key in fields:
        texts.extend(df[COLS[key]].astype(str).tolist())
    return score_sentiment_texts(texts)


# ================= FIXED: REAL RECOGNITION REACH =================
def recognition_reach_rate(df):
    col_aw = COLS["which_awards"]

    # Count only those who ACTUALLY received an award
    has_awards = df[col_aw].apply(lambda x: len(parse_awards(x)) > 0)

    total = len(df)
    if total == 0:
        return np.nan

    return float(has_awards.sum() / total * 100)


# ================= WORDCLOUD =================
def show_wordcloud(texts, title, colormap="viridis", phrase_cloud=False):
    if not _WORDCLOUD_OK:
        st.info("WordCloud not available.")
        return

    texts = [clean_text(t) for t in texts if t]
    if not texts:
        st.info(f"No data for {title}")
        return

    if phrase_cloud:
        trimmed = [" ".join(t.split()[:10]) for t in texts]
        freq = Counter(trimmed)
        wc = WordCloud(
            width=1100, height=400,
            background_color="white",
            colormap=colormap
        ).generate_from_frequencies(freq)
        fig, ax = plt.subplots(figsize=(14, 6))
    else:
        wc = WordCloud(
            width=1200, height=500,
            background_color="white",
            colormap=colormap
        ).generate(" ".join(texts))
        fig, ax = plt.subplots(figsize=(12, 5))

    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title)
    st.pyplot(fig)


# ================= KPI (NO DECIMALS, WITH ? ICON) =================
def safe_metric(v, label, help_text):
    display = "–" if np.isnan(v) else str(int(round(v)))
    st.markdown(
        f"""
        <div class="metric-card">
          <h4>
            <span class="kpi-label">
              {label}
              <span class="kpi-help" title="{help_text}">?</span>
            </span>
          </h4>
          <h2>{display}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


# ================= MAIN DASHBOARD =================
def show_rr_dashboard():
    st.markdown("<h1 style='text-align:center;'>🎯 R&R Survey Insights Dashboard</h1>", unsafe_allow_html=True)
    st.caption(
        "Comparing the earlier Town Hall-based R&R with the current Kudos Bot system "
        "using participant feedback, sentiment and recognition reach."
    )

    df = load_survey_data()

    # USE ALL PARTICIPANTS (FIX)
    survey_participants = df

    # KPI VALUES
    earlier_score = earlier_rating_score(survey_participants)
    current_score = current_sentiment_score(survey_participants)
    reach = recognition_reach_rate(survey_participants)
    lift = ((current_score - earlier_score) / earlier_score) * 100 if earlier_score else np.nan

    # KPI CARDS
    k = st.columns(4)

    with k[0]:
        safe_metric(
            earlier_score,
            "Earlier System Happiness Score",
            "Average rating (1–3) for the old Town Hall R&R, converted into a 0–100 score."
        )

    with k[1]:
        safe_metric(
            current_score,
            "Current System Happiness Score",
            "Sentiment score for the Kudos Bot system based on open-text responses."
        )

    with k[2]:
        safe_metric(
            reach,
            "How Many People Got Recognized",
            "Percentage of all survey participants who actually received at least one award."
        )

    with k[3]:
        safe_metric(
            lift,
            "Improvement From Earlier System",
            "Relative % change in happiness: (Current − Earlier) ÷ Earlier × 100."
        )

    st.divider()

    # Engagement
    st.markdown("<p class='section-title'>👀 Which version feels more engaging?</p>", unsafe_allow_html=True)

    map_eng = {
        "Earlier system (Town Hall via Google Meet)": "Earlier",
        "Current system (Kudos Bot in Chat)": "Current",
        "Both equally engaging": "Both",
    }

    mapped = survey_participants[COLS["engaging"]].map(
        lambda x: map_eng.get(str(x).strip(), "Other")
    )

    df_eng = pd.DataFrame({
        "Engaging": ["Earlier", "Current"],
        "Count": [(mapped == "Earlier").sum(), (mapped == "Current").sum()]
    })

    fig_eng = px.pie(
        df_eng, names="Engaging", values="Count",
        title="Earlier vs Current — Engagement Preference",
        color="Engaging",
        color_discrete_map={"Earlier": "#1f77b4", "Current": "#ff4136"}
    )
    st.plotly_chart(fig_eng, use_container_width=True)

    st.info(f"⭐ **Both equally engaging**: { (mapped == 'Both').sum() } respondents")

    st.divider()

    # Awards
    st.markdown("<p class='section-title'>🏅 Who is getting recognised?</p>", unsafe_allow_html=True)

    awards = []
    for v in survey_participants[COLS["which_awards"]].tolist():
        awards.extend(parse_awards(v))

    if awards:
        counts = pd.Series(awards).value_counts().reset_index()
        counts.columns = ["Award", "Recognitions"]
        fig_aw = px.bar(
            counts, x="Award", y="Recognitions",
            title="Recognitions by Award Type"
        )
        fig_aw.update_layout(template="plotly_white")
        st.plotly_chart(fig_aw, use_container_width=True)
    else:
        st.info("No valid award data to display.")

    st.divider()

    # =====================================================
    # WORD MAPS — DIFFERENT COLORS + REMOVE NAN/NO/NONE
    # =====================================================
    st.markdown("<p class='section-title'>🧠 What people liked — Earlier vs Current</p>", unsafe_allow_html=True)

    # Earlier likes
    earlier_likes = [
        t.strip() for t in survey_participants[COLS["earlier_like"]].astype(str).tolist()
        if t.strip().lower() not in {"na", "none", "no", "-", "nil", "nan", ""}
    ]

    # Current likes
    current_likes = [
        t.strip() for t in survey_participants[COLS["like_current"]].astype(str).tolist()
        if t.strip().lower() not in {"na", "none", "no", "-", "nil", "nan", ""}
    ]

    c1, c2 = st.columns(2)
    with c1:
        show_wordcloud(earlier_likes, "Earlier System — Likes", colormap="Blues")
    with c2:
        show_wordcloud(current_likes, "Current System — Likes", colormap="Oranges")

    st.divider()

    # =====================================================
    # IMPROVEMENT SUGGESTIONS — REMOVE USELESS TEXT
    # =====================================================
    st.markdown("<p class='section-title'>🔧 Key improvement suggestions</p>", unsafe_allow_html=True)

    raw_improvements = survey_participants[COLS["improve_current"]].astype(str).tolist()

    bad_words = {
        "na", "n/a", "none", "no", "nil", "nan", "-", "",
        "no suggestions", "no suggestion", "no comments",
        "nothing", "not applicable", "null"
    }

    improvements = [
        t.strip()
        for t in raw_improvements
        if t.strip().lower() not in bad_words
    ]

    show_wordcloud(
        improvements,
        "Improvement Suggestions",
        colormap="Purples",
        phrase_cloud=True
    )

    st.caption("Wordclouds cleaned: NAN/none/no/nil removed, each section uses distinct color palettes.")


# RUN
if __name__ == "__main__":
    show_rr_dashboard()
