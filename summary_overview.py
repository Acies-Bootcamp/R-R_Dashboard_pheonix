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


# ================= GLASS UI =================
glass_css = """
<style>
.metric-card {
  background: rgba(255,255,255,0.25);
  border-radius: 24px;
  box-shadow: 0 8px 32px 0 rgba(31,38,135,0.12);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.18);
  padding: 28px 20px 16px 20px;
  margin-bottom: 24px;
  text-align:center;
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


# ================= KPI (NO DECIMALS) =================
def safe_metric(v, label, help_text):
    display = "–" if np.isnan(v) else str(int(round(v)))
    st.markdown(
        f'<div class="metric-card"><h4>{label}</h4>'
        f'<p title="{help_text}"><b>{display}</b></p></div>',
        unsafe_allow_html=True
    )


# ================= MAIN DASHBOARD =================
def show_rr_dashboard():
    st.title("R&R Metrics Dashboard")

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
        safe_metric(earlier_score, "Earlier System Happiness Score",
                    "How happy people were with the old Town Hall R&R")

    with k[1]:
        safe_metric(current_score, "Current System Happiness Score",
                    "How happy people are with the Kudos Bot system")

    with k[2]:
        safe_metric(reach, "How Many People Got Recognized",
                    "Percentage of ALL survey participants who actually received an award")

    with k[3]:
        safe_metric(lift, "Improvement From Earlier System",
                    "Increase or drop in happiness")

    st.divider()

    # Engagement
    st.subheader("Which version is more engaging?")

    map_eng = {
        "Earlier system (Town Hall via Google Meet)": "Earlier",
        "Current system (Kudos Bot in Chat)": "Current",
        "Both equally engaging": "Both",
    }

    mapped = survey_participants[COLS["engaging"]].map(lambda x: map_eng.get(str(x).strip(), "Other"))

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

    st.info(f"Both Equally Engaging: {(mapped == 'Both').sum()} respondents")

    st.divider()

    # Awards
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
        st.plotly_chart(fig_aw, use_container_width=True)

    st.divider()

    # =====================================================
    # WORD MAPS — DIFFERENT COLORS + REMOVE NAN/NO/NONE
    # =====================================================
    st.subheader("Word Maps — Earlier vs Current System")

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
    st.subheader("Key Improvement Suggestions")

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

    show_wordcloud(improvements, "Improvement Suggestions", colormap="Purples", phrase_cloud=True)

    st.caption("Wordclouds cleaned: NAN/none/no/nil removed, each section uses different colors.")


# RUN
if __name__ == "__main__":
    show_rr_dashboard()