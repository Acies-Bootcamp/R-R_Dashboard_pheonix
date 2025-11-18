# summary_overview.py
import os
import re
import html
import json
import styles
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from collections import Counter
from io import BytesIO

# Optional Gemini (Google) integration
try:
    import google.generativeai as genai
    GEMINI_OK = True
except Exception:
    GEMINI_OK = False

# Ensure VADER is present
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

# WordCloud availability
_WORDCLOUD_OK = True
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
except Exception:
    _WORDCLOUD_OK = False


# ====================== SMART REPHRASING LAYER ======================
def clean_rephrase(text: str) -> str:
    """
    Convert raw phrase/theme into a short improvement suggestion.
    Does NOT rewrite the user sentence.
    Only maps to a short category.
    """
    if text is None:
        return ""
    t = str(text).strip().lower()
    if not t:
        return ""

    mapping = {
        ("communicat", "inform", "announce", "notify"): "Better communication",
        ("recognition", "appreciation", "reward", "recognise"): "Improve recognition process",
        ("delay", "late", "slow", "approval", "approvals"): "Reduce delays",
        ("visible", "visibility", "see", "noticed"): "More visibility",
        ("transparent", "clarity", "clear"): "Increase transparency",
        ("workflow", "process", "steps", "procedure"): "Improve process",
        ("fast", "quick", "speed", "faster"): "Faster process",
        ("support", "help", "assist"): "More support required",
        ("feedback", "suggestion", "input"): "More constructive feedback",
        ("engage", "interesting", "fun", "interactive"): "Increase engagement",
        ("ux", "interface", "design", "user experience"): "Improve user experience",
        ("fair", "bias", "equal"): "Ensure fairness",
        ("train", "onboard", "learn"): "Better training",
    }

    for keys, category in mapping.items():
        if any(k in t for k in keys):
            return category

    # If no mapping found — fallback to original (lightly cleaned)
    return t.capitalize()



# ================= GLASS / MONOCHROME UI CSS =================
glass_css = """
<style>
body {
    background-color: #f5f5f5;
    color: #222222;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.main > div { padding-top: 0.5rem; }
h1, h2, h3, h4 { color: #222222 !important; }

/* Metric card */
.metric-card {
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(15,23,42,0.08);
  border: 1px solid #e5e7eb;
  padding: 20px 18px 14px 18px;
  margin-bottom: 20px;
  text-align:center;
}
.metric-card h4 { font-size: 0.95rem; font-weight: 600; color: #6b7280; margin-bottom: 0.4rem; }
.metric-card h2 { font-size: 1.7rem; font-weight: 700; color: #111827; margin: 0; }

/* KPI help */
.kpi-label { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.kpi-help { position: relative; font-size: 0.75rem; color: #6b7280; border-radius: 999px; border: 1px solid #d4d4d8; width: 16px; height: 16px; display: inline-flex; align-items: center; justify-content: center; cursor: help; background-color: #f9fafb; }
.kpi-help::after { content: attr(data-tip); position: absolute; left: 50%; bottom: 125%; transform: translateX(-50%); background: #111827; color: #f9fafb; padding: 6px 10px; border-radius: 6px; font-size: 0.75rem; line-height: 1.2; white-space: normal; min-width: 180px; max-width: 260px; text-align: left; opacity: 0; pointer-events: none; transition: opacity 0.15s ease-out; z-index: 9999; }
.kpi-help::before { content: ""; position: absolute; left: 50%; bottom: 115%; transform: translateX(-50%); border-width: 5px; border-style: solid; border-color: #111827 transparent transparent transparent; opacity: 0; transition: opacity 0.15s ease-out; }
.kpi-help:hover::after, .kpi-help:hover::before { opacity: 1; }

/* Plot wrapper */
.stPlotlyChart { background: radial-gradient(circle at top left, rgba(255,255,255,0.96), rgba(243,244,246,1)); border-radius: 16px; padding: 12px; border: 1px solid rgba(209,213,219,0.9); box-shadow: 0 10px 30px rgba(15,23,42,0.12); }

/* Section titles */
.section-title { font-weight: 600; font-size: 1.05rem; color: #374151; margin-bottom: 0.4rem; }
</style>
"""


# ================= COLUMN KEYS =================
COLS = {
    "timestamp": "Timestamp",
    "team": "Team Name",
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


# ================= SCORE HELPERS =================
def earlier_rating_score(df: pd.DataFrame):
    s = pd.to_numeric(df[COLS["earlier_rating"]], errors="coerce")
    return float((s.mean() / 3) * 100) if not s.dropna().empty else np.nan


def score_sentiment_texts(texts):
    texts = [clean_text(t) for t in texts if clean_text(t)]
    if not texts:
        return np.nan
    sia = SentimentIntensityAnalyzer()
    vals = [(sia.polarity_scores(t)["compound"] + 1) / 2 * 100 for t in texts]
    return float(np.mean(vals))


def current_sentiment_score(df: pd.DataFrame):
    fields = ["like_current", "improve_current", "comments_any"]
    texts = []
    for key in fields:
        texts.extend(df[COLS[key]].astype(str).tolist())
    return score_sentiment_texts(texts)


def recognition_reach_rate(df: pd.DataFrame):
    col_aw = COLS["which_awards"]
    has_awards = df[col_aw].apply(lambda x: len(parse_awards(x)) > 0)
    total = len(df)
    return float(has_awards.sum() / total * 100) if total else np.nan


# ================= COLOR HELPERS =================
def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def _make_freq_color_func(freq_dict, colormap_name: str):
    if colormap_name.lower() == "blues":
        light_hex, dark_hex = "#bfdbfe", "#1d4ed8"
    elif colormap_name.lower() == "oranges":
        light_hex, dark_hex = "#fed7aa", "#c2410c"
    elif colormap_name.lower() == "spectral":
        light_hex, dark_hex = "#fee2e2", "#b91c1c"
    else:
        light_hex, dark_hex = "#e5e7eb", "#4b5563"

    light_rgb = _hex_to_rgb(light_hex)
    dark_rgb = _hex_to_rgb(dark_hex)
    max_freq = max(freq_dict.values()) if freq_dict else 1.0

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        f = freq_dict.get(word, 0.0) / max_freq
        f = f ** 0.5
        r = int(light_rgb[0] + (dark_rgb[0] - light_rgb[0]) * f)
        g = int(light_rgb[1] + (dark_rgb[1] - light_rgb[1]) * f)
        b = int(light_rgb[2] + (dark_rgb[2] - light_rgb[2]) * f)
        return _rgb_to_hex((r, g, b))

    return color_func


# ================= GEMINI CLUSTERING =================
def _extract_json_block(text: str) -> str | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return None


def gemini_cluster_phrases(phrases, section_name: str):
    freq = Counter(phrases)
    unique_phrases = list(freq.keys())

    default_mapping = [{"theme": p, "phrases": [p]} for p in unique_phrases]

    if not GEMINI_OK or not unique_phrases:
        mapping = default_mapping
    else:
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            sample_text = "\n".join(f"- {p}" for p in unique_phrases[:120])

            prompt = f"""
You are analysing employee survey feedback for section: "{section_name}".

Group similar phrases into themes. Respond ONLY with JSON in the form:

{{
  "clusters": [
    {{
      "theme": "short 3-6 word label",
      "phrases": ["original phrase 1", "original phrase 2", ...]
    }},
    ...
  ]
}}

Important rules:
- Use the original phrases EXACTLY in "phrases".
- Do NOT add any commentary outside the JSON.
- Do NOT invent new phrases.

Phrases:
{sample_text}
"""
            resp = model.generate_content(prompt)
            raw = resp.text or ""
            json_block = _extract_json_block(raw) or raw
            data = json.loads(json_block)
            mapping = data.get("clusters", default_mapping) or default_mapping
        except Exception:
            mapping = default_mapping

    phrase_to_theme: dict[str, str] = {}
    theme_freq: Counter[str] = Counter()

    for cl in mapping:
        theme_raw = cl.get("theme") or ""
        theme = clean_rephrase(theme_raw)
        if not theme:
            continue

        for p in cl.get("phrases", []):
            p_clean = str(p).strip()
            if not p_clean:
                continue
            if p_clean in freq:
                # Map original phrase -> cleaned theme
                phrase_to_theme[p_clean] = theme
                theme_freq[theme] += freq[p_clean]

    # ensure every phrase has a theme
    for p, c in freq.items():
        if p not in phrase_to_theme:
            theme_clean = clean_rephrase(p)
            phrase_to_theme[p] = theme_clean
            theme_freq[theme_clean] += c

    return theme_freq, phrase_to_theme, freq


# ================= WORDCLOUD =================
def show_wordcloud(texts, title, colormap: str = "viridis", phrase_cloud: bool = False):
    if not _WORDCLOUD_OK:
        st.info("WordCloud not available.")
        return

    # Ensure texts are strings and strip
    texts = [clean_text(t) for t in texts if clean_text(t)]
    if not texts:
        st.info(f"No data for {title}")
        return

    section_name = title

    if phrase_cloud:
        parts = []
        noise = {
            "na", "n/a", "none", "no", "-", "nil", "nan",
            "neutral", "not sure", "no idea", "cant say", "can't say",
        }

        for t in texts:
            t = t.replace("\r", " ").replace("\n", " ")
            chunks = re.split(r"[;,/]", t)
            for ch in chunks:
                p = " ".join(str(ch).strip().split())
                if p and p.lower() not in noise:
                    parts.append(p)

        if not parts:
            st.info(f"No usable phrases for {title}")
            return

        # Cluster phrases into themes (Gemini if available)
        theme_freq, phrase_to_theme, raw_freq = gemini_cluster_phrases(parts, section_name)

        # Store mapping for Excel download — ONLY for Improvement Suggestions
        if section_name == "Improvement Suggestions":
            rows = []
            for phrase, count in raw_freq.items():
                theme_raw = phrase_to_theme.get(phrase, phrase)
                rows.append(
                    {
                        "Section": section_name,
                        "Original Phrase": phrase,  # keep original untouched
                        "Count": count,
                        "Theme (Cleaned)": clean_rephrase(theme_raw),
                    }
                )

            df_map = pd.DataFrame(rows)
            maps = st.session_state.setdefault("phrase_maps", [])
            maps.append(df_map)

        wc = WordCloud(
            width=1400,
            height=450,
            background_color="white",
            max_words=len(theme_freq),
            prefer_horizontal=0.95,
            collocations=False,
            random_state=42,
        ).generate_from_frequencies(theme_freq)

        wc = wc.recolor(color_func=_make_freq_color_func(theme_freq, colormap))

        fig, ax = plt.subplots(figsize=(14, 4.5))
    else:
        text_blob = " ".join(texts)
        wc = WordCloud(
            width=1400,
            height=450,
            background_color="white",
            colormap=colormap,
            prefer_horizontal=0.95,
            collocations=False,
            max_words=500,
            min_font_size=12,
            relative_scaling=1.0,
            random_state=42,
        ).generate(text_blob)
        fig, ax = plt.subplots(figsize=(14, 4.5))

    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title)
    st.pyplot(fig)


# ================= KPI DISPLAY =================
def safe_metric(v, label, help_text, suffix: str = ""):
    tip = html.escape(str(help_text), quote=True)

    if v is None:
        display = "–"
    else:
        try:
            val = float(v)
            if np.isnan(val):
                display = "–"
            else:
                display = f"{int(round(val))}{suffix}"
        except Exception:
            display = f"{v}{suffix}"

    st.markdown(
        f"""
        <div class="metric-card">
          <h4>
            <span class="kpi-label">
              {label}
              <span class="kpi-help" data-tip="{tip}">?</span>
            </span>
          </h4>
          <h2>{display}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


# ================= SAFELY CLEAN LIST UTILITY =================
def clean_list(values):
    """Return a cleaned list of non-empty, non-noise strings from values."""
    bad = {"", "na", "n/a", "-", "none", "nil", "nan", "no suggestions", "nothing", "no", "no comments"}
    out = []
    for v in values:
        v_str = "" if pd.isna(v) else str(v).strip()
        if v_str and v_str.lower() not in bad:
            out.append(v_str)
    return out


# ================= MAIN DASHBOARD =================
def show_rr_dashboard():
    # reset phrase maps each run
    st.session_state["phrase_maps"] = []

    # Apply global styles using the selected theme
    theme = st.session_state.get("theme", "Blue")
    try:
        styles.apply_styles(theme=theme)
    except Exception:
        pass
    st.markdown(glass_css, unsafe_allow_html=True)

    st.caption(
        "Comparing the earlier Town Hall-based R&R with the current Kudos Bot system "
        "using participant feedback, sentiment and recognition reach."
    )

    df = load_survey_data()
    survey_participants = df

    # KPI VALUES
    earlier_score = earlier_rating_score(survey_participants)
    current_score = current_sentiment_score(survey_participants)
    reach = recognition_reach_rate(survey_participants)

    if earlier_score is not None and not np.isnan(earlier_score):
        try:
            lift = ((current_score - earlier_score) / earlier_score) * 100
        except Exception:
            lift = np.nan
    else:
        lift = np.nan

    # KPI CARDS
    k = st.columns(4)

    with k[0]:
        safe_metric(
            earlier_score,
            "Earlier System Happiness Score (/100)",
            (
                "Average rating for the old Town Hall R&R on a 1–3 scale, "
                "rescaled to a 0–100 happiness score. "
                "Unit: score out of 100 (/100)."
            ),
            suffix="/100",
        )

    with k[1]:
        safe_metric(
            current_score,
            "Current System Happiness Score (/100)",
            (
                "VADER sentiment on all comments about the current Kudos Bot system. "
                "The compound score (−1 to +1) is converted to a 0–100 index using: "
                "((compound + 1) / 2) × 100. "
                "Unit: score out of 100 (/100)."
            ),
            suffix="/100",
        )

    with k[2]:
        safe_metric(
            reach,
            "How Many People Got Recognized (%)",
            (
                "Percentage of all survey respondents who say they have received "
                "at least one award (based on the 'Which award(s) have you received?' question). "
                "Unit: percentage of respondents (%)."
            ),
            suffix="%",
        )

    with k[3]:
        safe_metric(
            lift,
            "Current System Effectiveness (%)",
            (
                "Relative change in happiness between the current Kudos Bot system and the earlier "
                "Town Hall system. Formula: ((Current Score − Earlier Score) ÷ Earlier Score) × 100. "
                "Unit: percentage change (%)."
            ),
            suffix="%",
        )

    st.caption(
        "Happiness metrics are on a 0–100 scale (/100). "
        "'Current System Effectiveness (%)' shows how much the current system improves or drops "
        "vs the earlier one."
    )

    st.divider()

    # Engagement preference
    st.markdown("<p class='section-title'>👀 Which version feels more engaging?</p>", unsafe_allow_html=True)

    map_eng = {
        "Earlier system (Town Hall via Google Meet)": "Earlier",
        "Current system (Kudos Bot in Chat)": "Current",
        "Both equally engaging": "Both",
    }

    mapped = survey_participants[COLS["engaging"]].map(
        lambda x: map_eng.get(str(x).strip(), "Other") if not pd.isna(x) else "Other"
    )

    label_map = {
        "Earlier": "All Hands (via G Meet)",
        "Current": "Kudos Corner (Kudos Bot)",
    }

    df_eng = pd.DataFrame({
        "Engaging": [
            label_map["Earlier"],
            label_map["Current"],
        ],
        "Count": [
            (mapped == "Earlier").sum(),
            (mapped == "Current").sum(),
        ],
    })

    fig_eng = px.pie(
        df_eng,
        names="Engaging",
        values="Count",
        title="All Hands vs Kudos Corner — Engagement Preference",
        color="Engaging",
        color_discrete_map={
            label_map["Earlier"]: "#2563EB",
            label_map["Current"]: "#EC4899",
        },
    )
    st.plotly_chart(fig_eng, use_container_width=True)

    st.info(f"⭐ **Both equally engaging**: { (mapped == 'Both').sum() } respondents")

    st.divider()

    # Awards (survey-based)
    st.markdown("<p class='section-title'>🏅 Who is getting recognised?</p>", unsafe_allow_html=True)

    awards = []
    for v in survey_participants[COLS["which_awards"]].tolist():
        awards.extend(parse_awards(v))

    if awards:
        counts = pd.Series(awards).value_counts().reset_index()
        counts.columns = ["Award", "Recognitions"]

        overview_palette = [
            "#2563EB",
            "#10B981",
            "#F59E0B",
            "#EC4899",
            "#8B5CF6",
        ]

        fig_aw = px.bar(
            counts,
            x="Award",
            y="Recognitions",
            color="Award",
            text="Recognitions",
            title="Recognitions by Award Type (Survey Responses)",
            color_discrete_sequence=overview_palette,
        )

        fig_aw.update_traces(
            textposition="outside",
            textfont_size=14,
            marker_line_width=0,
        )

        fig_aw.update_layout(
            template="plotly_white",
            height=420,
            margin=dict(l=40, r=30, t=60, b=60),
            xaxis_title="Award Type",
            yaxis_title="Number of Mentions in Survey",
            title_font_size=20,
            xaxis=dict(tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=13)),
            legend=dict(title_text="Award", font=dict(size=12)),
        )

        st.plotly_chart(fig_aw, use_container_width=True)
    else:
        st.info("No valid award data to display.")

    st.divider()

    # WORD MAPS – likes (Gemini themes)
    st.markdown("<p class='section-title'>🧠 What people liked — Earlier vs Current</p>", unsafe_allow_html=True)

    earlier_like_raw = survey_participants[COLS["earlier_like"]].astype(object).tolist()
    current_like_raw = survey_participants[COLS["like_current"]].astype(object).tolist()

    earlier_likes = clean_list(earlier_like_raw)
    current_likes = clean_list(current_like_raw)

    c1, c2 = st.columns(2)
    with c1:
        show_wordcloud(
            earlier_likes,
            "Earlier Likes",
            colormap="Blues",
            phrase_cloud=True,
        )
    with c2:
        show_wordcloud(
            current_likes,
            "Current Likes",
            colormap="Oranges",
            phrase_cloud=True,
        )

    st.divider()

    # IMPROVEMENTS – theme cloud
    st.markdown("<p class='section-title'>🔧 Key improvement suggestions</p>", unsafe_allow_html=True)

    raw_improvements = survey_participants[COLS["improve_current"]].astype(object).tolist()
    improvements = clean_list(raw_improvements)

    show_wordcloud(
        improvements,
        "Improvement Suggestions",
        colormap="Spectral",
        phrase_cloud=True,
    )

    st.caption(
        "Phrases are clustered into themes using Gemini (if available). "
        "Each word in the cloud is a theme label; size and colour reflect how many responses map to that theme."
    )

    # ================= EXCEL DOWNLOAD =================
    if st.session_state.get("phrase_maps"):
        all_maps = pd.concat(st.session_state["phrase_maps"], ignore_index=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for section, df_sec in all_maps.groupby("Section"):
                # Excel sheet names: max 31 chars, no special symbols
                sheet_name = re.sub(r"[^\w]", "_", section)[:31] or "Sheet1"
                df_sec.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)

        st.download_button(
            "⬇️ Download phrase → theme mapping (Excel)",
            data=output,
            file_name="rr_phrase_themes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# RUN
if __name__ == "__main__":
    show_rr_dashboard()
