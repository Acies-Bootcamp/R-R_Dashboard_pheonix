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


# Optional GROQ integration
try:
    from groq import Groq
    GROQ_OK = True
except Exception:
    GROQ_OK = False



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
.kpi-help::after { content: attr(data-tip); position: absolute; left: 50%; bottom: 125%; transform: translateX(-50%); background: #111827; color: #f9faff; padding: 6px 10px; border-radius: 6px; font-size: 0.75rem; line-height: 1.2; white-space: normal; min-width: 180px; max-width: 260px; text-align: left; opacity: 0; pointer-events: none; transition: opacity 0.15s ease-out; z-index: 9999; }
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
    fields = ["like_current", "improve_current"]
    texts = []
    for key in fields:
        texts.extend(df[COLS[key]].astype(str).tolist())
    return score_sentiment_texts(texts)




def recognition_reach_rate(df: pd.DataFrame):
    col = COLS["have_current"]  # "Have you ever received or given an award in the current Kudos Bot system?"
    s = df[col].astype(str).str.strip().str.lower()

    # consider only people who answered something
    answered = s[~s.isin(["", "nan"])]
    if answered.empty:
        return np.nan

    # treat these as "recognized in current system"
    yes_vals = {
        "yes", 
        "i have received", 
        "i have both given and received", 
        "both", 
        "given and received"
    }

    got_recognised = answered.isin(yes_vals)

    return float(got_recognised.sum() / len(answered) * 100)



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




# ================= AI CLUSTERING (ONLY FOR IMPROVEMENTS) =================
def gemini_cluster_phrases(phrases, section_name: str):
    """
    Use AI to rephrase suggestions while preserving exact meaning.
    ONLY used for Improvement Suggestions.
    """
    # ✅ HARDCODED API KEYS
    FALLBACK_GEMINI_KEY = "AIzaSyC43DGWdR3LJbxPvFXL9oZDTUA7f7wry_0"
    FALLBACK_GROQ_KEY = "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"
    
    freq = Counter(phrases)
    unique_phrases = list(freq.keys())

    default_mapping = [{"theme": p, "phrases": [p]} for p in unique_phrases]

    if not unique_phrases:
        return {}, {}, freq

    sample_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(unique_phrases[:150]))

    prompt = f"""
You are analyzing employee survey feedback for: "{section_name}".

Your task: REPHRASE each suggestion to be SHORTER while preserving EXACT meaning.

CRITICAL RULES:
1. **Preserve meaning**: The shortened version must mean EXACTLY the same thing
2. **Only group IDENTICAL suggestions**: If two phrases say the same thing differently, group them
3. **DO NOT merge different ideas**: If suggestions are about different topics, keep them separate
4. **Make it concise**: Use 3-6 words maximum for the rephrased version
5. **Use original phrases** in the "phrases" array - don't invent new ones

Return JSON in this exact format:
{{
  "clusters": [
    {{
      "theme": "Short rephrased version (3-6 words)",
      "phrases": ["original phrase 1", "original phrase 2"]
    }}
  ]
}}

Survey responses:
{sample_text}

JSON output:
"""

    mapping = default_mapping
    ai_used = "None"
    error_details = []  # ✅ COLLECT ALL ERRORS

    # TRY GEMINI FIRST
    if GEMINI_OK:
        try:
            gemini_api_key = os.environ.get("GEMINI_API_KEY") or FALLBACK_GEMINI_KEY
            
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                model_names = ["gemini-1.5-flash-002", "gemini-1.5-flash", "gemini-pro"]
                
                for model_name in model_names:
                    try:
                        model = genai.GenerativeModel(model_name)
                        resp = model.generate_content(prompt)
                        raw = resp.text or ""
                        
                        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            mapping = data.get("clusters", default_mapping) or default_mapping
                            ai_used = f"Gemini ({model_name})"
                            break
                    except Exception as e:
                        error_details.append(f"Gemini {model_name}: {str(e)[:150]}")
                        continue
                    
        except Exception as e:
            error_details.append(f"Gemini setup: {str(e)[:150]}")

    # FALLBACK TO GROQ
    if ai_used == "None" and GROQ_OK:
        try:
            groq_api_key = os.environ.get("GROQ_API_KEY") or FALLBACK_GROQ_KEY
            
            if groq_api_key:
                client = Groq(api_key=groq_api_key)
                groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
                
                for model_name in groq_models:
                    try:
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are an expert at analyzing survey feedback."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=4096,
                        )
                        
                        raw = completion.choices[0].message.content
                        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            mapping = data.get("clusters", default_mapping) or default_mapping
                            ai_used = f"GROQ ({model_name})"
                            break
                    except Exception as e:
                        error_details.append(f"GROQ {model_name}: {str(e)[:150]}")
                        continue
                    
        except Exception as e:
            error_details.append(f"GROQ setup: {str(e)[:150]}")

    # ✅ SHOW DETAILED STATUS
    if ai_used != "None":
        st.success(f"✅ AI-powered summarization by {ai_used}")
    else:
        # Show detailed error in expander
        with st.expander("⚠️ AI temporarily unavailable. Click to see error details"):
            st.warning("Using original phrases (no AI summarization).")
            st.markdown("**Detailed errors:**")
            for err in error_details:
                st.code(err)
            st.markdown("""
            **Possible fixes:**
            1. **Get fresh GROQ key**: https://console.groq.com/keys
            2. **Replace FALLBACK_GROQ_KEY** in code (line 266)
            3. **Restart Streamlit**
            """)

    # Build maps
    phrase_to_theme = {}
    theme_freq = Counter()

    for cl in mapping:
        theme = cl.get("theme", "").strip()
        if not theme:
            continue

        for p in cl.get("phrases", []):
            p_clean = str(p).strip()
            if p_clean in freq:
                phrase_to_theme[p_clean] = theme
                theme_freq[theme] += freq[p_clean]

    for p, c in freq.items():
        if p not in phrase_to_theme:
            phrase_to_theme[p] = p
            theme_freq[p] += c

    return theme_freq, phrase_to_theme, freq




# ================= WORDCLOUD =================
def show_wordcloud(texts, title, colormap: str = "viridis", phrase_cloud: bool = False, use_ai: bool = False):
    if not _WORDCLOUD_OK:
        st.info("WordCloud not available.")
        return

    texts = [clean_text(t) for t in texts if clean_text(t)]
    if not texts:
        st.info(f"No data for {title}")
        return

    section_name = title

    if phrase_cloud:
        parts = []
        noise = {"na", "n/a", "none", "no", "-", "nil", "nan", "neutral", "not sure", "no idea", "cant say", "can't say"}

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

        # ✅ ONLY USE AI IF use_ai=True
        if use_ai:
            theme_freq, phrase_to_theme, raw_freq = gemini_cluster_phrases(parts, section_name)
        else:
            # Regular frequency count (no AI)
            raw_freq = Counter(parts)
            theme_freq = raw_freq
            phrase_to_theme = {p: p for p in parts}

        # Store mapping for Excel (Improvements only)
        if section_name == "Improvement Suggestions" and use_ai:
            rows = []
            theme_to_phrases = {}

            for phrase, count in raw_freq.items():
                theme = phrase_to_theme.get(phrase, phrase)

                rows.append({
                    "Section": section_name,
                    "Original Phrase": phrase,
                    "Count": count,
                    "Theme (AI-Summarized)": theme,
                })

                bucket = theme_to_phrases.setdefault(theme, {"count": 0, "items": []})
                bucket["count"] += count
                bucket["items"].append((phrase, count))

            if rows:
                df_map = pd.DataFrame(rows)
                maps = st.session_state.setdefault("phrase_maps", [])
                maps.append(df_map)

            st.session_state["improvement_themes"] = theme_to_phrases

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
            display = f"{int(round(val))}{suffix}" if not np.isnan(val) else "–"
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
    bad = {"", "na", "n/a", "-", "none", "nil", "nan", "no suggestions", "nothing", "no", "no comments"}
    out = []
    for v in values:
        v_str = "" if pd.isna(v) else str(v).strip()
        if v_str and v_str.lower() not in bad:
            out.append(v_str)
    return out




# ================= MAIN DASHBOARD =================
def show_rr_dashboard():
    st.session_state["phrase_maps"] = []
    st.session_state["improvement_themes"] = {}

    theme = st.session_state.get("theme", "Blue")
    try:
        styles.apply_styles(theme=theme)
    except Exception:
        pass
    st.markdown(glass_css, unsafe_allow_html=True)

    df = load_survey_data()
    survey_participants = df
    response_count = len(survey_participants)

    # GREEN BANNER
    st.markdown(
        f"""
        <div style="
            background-color:#ecfdf3;
            border:1px solid #22c55e;
            border-radius:12px;
            padding:10px 14px;
            margin-bottom:12px;
            color:#166534;
            font-size:0.95rem;
            font-weight:500;
        ">
            This overview is based <strong>purely on the R&amp;R survey responses</strong>.
            All metrics and percentages are calculated from the
            <strong>{response_count}</strong> people who filled the survey, not the entire organisation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Comparing the earlier ALL-Hands R&R with the current Kudos Bot system "
        "using participant feedback, sentiment and recognition reach."
    )

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
            "Average rating for the old All-Hands R&R on a 1–3 scale, rescaled to a 0–100 happiness score.",
            suffix="/100",
        )

    with k[1]:
        safe_metric(
            current_score,
            "Current System Happiness Score (/100)",
            "VADER sentiment on all comments about the current Kudos Bot system. The compound score (−1 to +1) is converted to a 0–100 index.",
            suffix="/100",
        )

    with k[2]:
        safe_metric(
            reach,
            "People who got received atleast one award (%)",
            "Percentage of all survey respondents who say they have received at least one award.",
            suffix="%",
        )

    with k[3]:
        safe_metric(
            lift,
            "Current System Effectiveness (%)",
            "Relative change in happiness between the current Kudos Bot system and the earlier All-Hands system.",
            suffix="%",
        )

    st.caption(
        "Happiness metrics are on a 0–100 scale (/100). "
        "'Current System Effectiveness (%)' shows how much the current system improves or drops vs the earlier one."
    )

    st.divider()

    # ✅ ENGAGEMENT PIE CHART (WITH CUSTOM LABEL FOR "BOTH EQUALLY ENGAGING")
    st.markdown("<p class='section-title'>📊 Which version is more engaging?</p>", unsafe_allow_html=True)

    engaging_col = COLS["engaging"]
    if engaging_col in survey_participants.columns:
        engaging_data = survey_participants[engaging_col].value_counts().reset_index()
        engaging_data.columns = ["Version", "Count"]
        
        # ✅ FILTER OUT "Both are equally engaging" for pie chart
        both_engaging = engaging_data[engaging_data["Version"].str.contains("both", case=False, na=False)]
        both_count = both_engaging["Count"].sum() if not both_engaging.empty else 0
        
        # Only show "Earlier" vs "Current" in pie chart
        pie_data = engaging_data[~engaging_data["Version"].str.contains("both", case=False, na=False)]
        
        if not pie_data.empty:
            fig_pie = px.pie(
                pie_data,
                names="Version",
                values="Count",
                title="R&R Program Engagement Preference",
                color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"],
            )

            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="white", width=2)),
            )

            fig_pie.update_layout(
                template="plotly_white",
                height=400,
                margin=dict(l=20, r=20, t=60, b=20),
                title_font_size=18,
            )

            st.plotly_chart(fig_pie, use_container_width=True)
            
            # ✅ SHOW "BOTH EQUALLY ENGAGING" COUNT BELOW PIE CHART
            if both_count > 0:
                st.info(f"ℹ️ **{both_count} people** voted that both versions are equally engaging.")
        else:
            st.info("Engagement data not available.")


    st.divider()

    # Awards
    st.markdown("<p class='section-title'>🏅 Who is getting recognised?</p>", unsafe_allow_html=True)

    awards = []
    for v in survey_participants[COLS["which_awards"]].tolist():
        awards.extend(parse_awards(v))

    if awards:
        counts = pd.Series(awards).value_counts().reset_index()
        counts.columns = ["Award", "Recognitions"]

        overview_palette = ["#2563EB", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6"]

        fig_aw = px.bar(
            counts,
            x="Award",
            y="Recognitions",
            color="Award",
            text="Recognitions",
            title="Recognitions by Award Type (Survey Responses)",
            color_discrete_sequence=overview_palette,
        )

        fig_aw.update_traces(textposition="outside", textfont_size=14, marker_line_width=0)
        fig_aw.update_layout(
            template="plotly_white",
            height=420,
            margin=dict(l=40, r=30, t=60, b=60),
            xaxis_title="Award Type",
            yaxis_title="Number of Mentions in Survey",
            title_font_size=20,
        )

        st.plotly_chart(fig_aw, use_container_width=True)
    else:
        st.info("No valid award data to display.")

    st.divider()

    # ✅ LIKES - NO AI
    st.markdown("<p class='section-title'>🧠 What people liked — Earlier vs Current</p>", unsafe_allow_html=True)

    earlier_like_raw = survey_participants[COLS["earlier_like"]].astype(object).tolist()
    current_like_raw = survey_participants[COLS["like_current"]].astype(object).tolist()

    earlier_likes = clean_list(earlier_like_raw)
    current_likes = clean_list(current_like_raw)

    c1, c2 = st.columns(2)
    with c1:
        show_wordcloud(earlier_likes, "Earlier Likes", colormap="Blues", phrase_cloud=True, use_ai=False)
    with c2:
        show_wordcloud(current_likes, "Current Likes", colormap="Oranges", phrase_cloud=True, use_ai=False)

    st.divider()

    # ✅ IMPROVEMENTS - WITH AI
    st.markdown("<p class='section-title'>🔧 Key improvement suggestions</p>", unsafe_allow_html=True)

    raw_improvements = survey_participants[COLS["improve_current"]].astype(object).tolist()
    improvements = clean_list(raw_improvements)

    show_wordcloud(improvements, "Improvement Suggestions", colormap="Spectral", phrase_cloud=True, use_ai=True)

    st.caption(
        "Phrases are AI-summarized to preserve meaning while being concise. "
        "Each word in the cloud is a condensed version; size and colour reflect frequency."
    )

    # THEME EXPLORER
    themes_data = st.session_state.get("improvement_themes") or {}

    if themes_data:
        st.markdown("#### Explore improvement suggestions by theme")
        with st.expander("View summarized themes with original comments", expanded=False):
            for theme in sorted(themes_data.keys(), key=lambda t: themes_data[t]["count"], reverse=True):
                bucket = themes_data[theme]
                total_count = bucket["count"]
                items = sorted(bucket["items"], key=lambda x: x[1], reverse=True)

                st.markdown(f"**{theme} ({total_count} responses)**")
                for phrase, count in items:
                    st.markdown(f"- **{count}×** {phrase}")
                st.markdown("---")

    if st.session_state.get("phrase_maps"):
        all_maps = pd.concat(st.session_state["phrase_maps"], ignore_index=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for section, df_sec in all_maps.groupby("Section"):
                sheet_name = re.sub(r"[^\w]", "_", section)[:31] or "Sheet1"
                df_sec.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)

        st.download_button(
            "⬇️ Download phrase → theme mapping (Excel)",
            data=output,
            file_name="phrase_themes_ai_summarized.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# RUN
if __name__ == "__main__":
    show_rr_dashboard()
