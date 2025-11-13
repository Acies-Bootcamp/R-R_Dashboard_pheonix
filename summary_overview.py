import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob   # <-- SENTIMENT ANALYSIS

# ==============================
# 🎨 Color Palette
# ==============================
COLOR_PALETTE = ['#A7C7E7', '#F4C2C2', '#C3E6CB', '#FFFACD', '#D8BFD8']

# ==============================
# 🧩 Load Data
# ==============================
@st.cache_data
def load_survey_data():
    sheet_key = "1KSuP5YlzyI1jdVTMMu5v7MLyzvP9Emr3Fo94BsiSFo0"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv"
    
    df = pd.read_csv(csv_url, on_bad_lines='skip', engine='python', encoding='utf-8')
    df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '')
    return df


# ==============================
# 🎨 Helper: Safe Column Finder
# ==============================
def find_column(df, keyword):
    cols = [c for c in df.columns if keyword.lower() in c.lower()]
    if cols:
        return cols[0]
    else:
        st.error(f"⚠️ Could not find a column containing: '{keyword}'")
        st.write("🧾 Available columns:", list(df.columns))
        st.stop()


# ==============================
# 🎨 Sentiment Helper
# ==============================
def sentiment_score(text):
    if pd.isna(text) or text.strip() == "":
        return 0
    return TextBlob(text).sentiment.polarity  # -1 to +1


# ==============================
# 🎨 Main Summary Overview
# ==============================
def show_summary_overview():

    st.markdown("""
        <h2 style='text-align:center; color:#2E4053;'>
            💎 Overall Effectiveness Snapshot
        </h2>
        <p style='text-align:center; color:gray; font-size:16px;'>
            Comparing engagement, awareness, and satisfaction between the <b>Earlier Town Hall R&R</b> 
            and the <b>Current Kudos Bot System</b>.
        </p>
    """, unsafe_allow_html=True)

    df = load_survey_data()

    # ==============================
    # 🎯 KPI CARDS (Original)
    # ==============================
    col1, col2, col3 = st.columns(3)

    # --- Avg Rating ---
    rating_col = find_column(df, "rate your overall experience")
    avg_rating = df[rating_col].dropna().astype(float).mean().round(1)

    with col1:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#A7C7E7,#D6EAF8);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 10px rgba(0,0,0,0.1);'>
                <h4 style='color:#2E4053;'>⭐ Avg. Rating (Earlier R&R)</h4>
                <h1 style='color:#154360;font-size:42px;'>{avg_rating} / 3</h1>
                <p style='color:gray;font-size:14px;'>Average satisfaction score</p>
            </div>
        """, unsafe_allow_html=True)

    # --- Participation ---
    award_col = find_column(df, "received or given an award")
    received_award = (df[award_col].astype(str).str.lower() == 'yes').mean() * 100

    with col2:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#A9DFBF,#D5F5E3);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 10px rgba(0,0,0,0.1);'>
                <h4 style='color:#2E4053;'>🏅 Participation in Current R&R</h4>
                <h1 style='color:#145A32;font-size:42px;'>{received_award:.1f}%</h1>
                <p style='color:gray;font-size:14px;'>Users who have given/received awards</p>
            </div>
        """, unsafe_allow_html=True)

    # --- Awareness ---
    aware_col = find_column(df, "aware of the earlier")
    aware_pct = round((df[aware_col].astype(str).str.lower() == 'yes').mean() * 100, 1)

    with col3:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#F5B7B1,#FADBD8);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 10px rgba(0,0,0,0.1);'>
                <h4 style='color:#2E4053;'>🎓 Awareness of Earlier System</h4>
                <h1 style='color:#7B241C;font-size:42px;'>{aware_pct}%</h1>
                <p style='color:gray;font-size:14px;'>Respondents aware of earlier R&R</p>
            </div>
        """, unsafe_allow_html=True)

    # =======================================================
    # 🎯 SENTIMENT KPI CARDS (NEW — INTEGRATED HERE)
    # =======================================================

    # Identify columns for sentiment
    earlier_like_col = find_column(df, "What did you like most about the earlier")
    current_like_col = find_column(df, "What do you like most about the current")
    improve_col = find_column(df, "improvements would you like to see")

    # Compute sentiment
    df["Earlier_Sentiment"] = df[earlier_like_col].apply(sentiment_score)
    df["Current_Sentiment"] = df[current_like_col].apply(sentiment_score)
    df["Improvement_Sentiment"] = df[improve_col].apply(sentiment_score)

    earlier_sent_avg = df["Earlier_Sentiment"].mean()
    current_sent_avg = df["Current_Sentiment"].mean()
    improve_sent_avg = df["Improvement_Sentiment"].mean()

    st.markdown("""
        <h3 style='text-align:center; margin-top:40px; color:#2E4053;'>
            🧠 Sentiment Overview — Emotional Perception of Each System
        </h3>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#AED6F1,#D6EAF8);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 12px rgba(0,0,0,0.1);'>
                <h4 style='color:#1B4F72;'>Earlier System Sentiment</h4>
                <h1 style='color:#154360;font-size:42px;'>{earlier_sent_avg:.2f}</h1>
                <p style='color:#566573;font-size:14px;'>Emotion Score (-1 to +1)</p>
            </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#A3E4D7,#D5F5E3);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 12px rgba(0,0,0,0.1);'>
                <h4 style='color:#0E6251;'>Current System Sentiment</h4>
                <h1 style='color:#117864;font-size:42px;'>{current_sent_avg:.2f}</h1>
                <p style='color:#566573;font-size:14px;'>Emotion Score (-1 to +1)</p>
            </div>
        """, unsafe_allow_html=True)

    with s3:
        st.markdown(f"""
            <div style='background:linear-gradient(135deg,#F5B7B1,#FADBD8);
                        padding:20px;border-radius:15px;text-align:center;
                        box-shadow:0px 4px 12px rgba(0,0,0,0.1);'>
                <h4 style='color:#7B241C;'>Improvement Sentiment</h4>
                <h1 style='color:#A93226;font-size:42px;'>{improve_sent_avg:.2f}</h1>
                <p style='color:#566573;font-size:14px;'>Lower = More Frustration</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)


    # ==============================
    # 🥇 Preference Pie Chart
    # ==============================
    st.markdown("""
        <h3 style='color:#1F618D;'>🎯 Which version of the R&R Program is more engaging?</h3>
    """, unsafe_allow_html=True)

    pref_col = find_column(df, "find more engaging")
    pref_data = df[pref_col].value_counts().reset_index()
    pref_data.columns = ['R&R Version', 'Responses']

    fig_pref = px.pie(
        pref_data,
        values='Responses',
        names='R&R Version',
        color='R&R Version',
        color_discrete_map={
            'Earlier system (Town Hall via Google Meet)': '#5B9BD5',
            'Current system (Kudos Bot in Chat)': '#E74C3C',
            'Both equally engaging': '#F4D03F'
        },
        hole=0.45
    )

    st.plotly_chart(fig_pref, use_container_width=True)

    # ==============================
    # 🔶 USER EXPERIENCE COMPARISON
    # ==============================

    st.markdown("""
        <h2 style='color:#2874A6;'>🔶 2️⃣ USER EXPERIENCE COMPARISON</h2>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    earlier_col = find_column(df, "What did you like most about the earlier")
    current_col = find_column(df, "What do you like most about the current")

    # WC Earlier
    text_earlier = " ".join(df[earlier_col].dropna().astype(str))
    wc1 = WordCloud(width=800, height=450, background_color='white', colormap='Blues').generate(text_earlier)

    with col1:
        st.markdown("#### 🕰️ Earlier R&R Likes")
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.imshow(wc1, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

    # WC Current
    text_curr = " ".join(df[current_col].dropna().astype(str))
    wc2 = WordCloud(width=800, height=450, background_color='white', colormap='Greens').generate(text_curr)

    with col2:
        st.markdown("#### ⚡ Current R&R Likes")
        fig2, ax2 = plt.subplots(figsize=(8, 4.5))
        ax2.imshow(wc2, interpolation='bilinear')
        ax2.axis('off')
        st.pyplot(fig2)

    # ==============================
    # Specialness Bar Chart
    # ==============================
    st.markdown("### 💭 Did Kudos Corner Feel as Special as All Hands?")
    
    special_col = find_column(df, "kudos corner")
    special_data = df[special_col].value_counts().reset_index()
    special_data.columns = ['Response', 'Count']

    fig_special = px.bar(
        special_data, x='Response', y='Count', text='Count',
        color='Response',
        color_discrete_sequence=['#A7C7E7', '#F4C2C2', '#FFFACD']
    )
    st.plotly_chart(fig_special, use_container_width=True)

    


# ==============================
# Run
# ==============================
if __name__ == "__main__":
    show_summary_overview()
