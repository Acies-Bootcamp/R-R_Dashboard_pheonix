import streamlit as st
from utils import load_css   # ⭐ Import CSS loader


def show_home_page():

    # ⭐ Load global CSS theme first
    load_css()

    st.title("🏆 Rewards & Recognition Dashboard")
    st.caption("Developed as part of the Capstone Project • November 2025")

    # --- Introduction ---
    st.markdown("""
    Welcome to the **Rewards & Recognition (R&R) Dashboard** — a comprehensive platform designed to analyze and visualize how recognition flows across teams and individuals within the organization.  
    The application helps evaluate the transition from the *Old Mentor-Based System* to the *New Peer-to-Peer Model* launched in June 2025.
    """)

    st.markdown("---")
    st.markdown("### 🎯 Purpose")
    st.markdown("""
    The R&R Dashboard aims to:
    - Understand the **effectiveness and fairness** of the new recognition process.  
    - Identify **team and individual performance trends** across departments.  
    - Assess how **award titles** are distributed and utilized under the new system.  
    - **Forecast recognition requirements** for future quarters based on past data trends.  
    """)

    st.markdown("---")
    st.markdown("### ⚙️ Key Modules in This Dashboard")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **🏅 Recognition Module**  
        - Explore awards at both **Team** and **Individual** levels.  
        - Track engagement, participation, and nomination sources.  
        """)
    with c2:
        st.markdown("""
        **📊 Award Analysis Module**  
        - Examine frequency and distribution of different award titles.  
        - Identify patterns and category dominance across teams.  
        """)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        **📈 Coupon Forecasting Module**  
        - Predict the **number of coupons** required for the upcoming quarter.  
        - Uses time-series models such as SARIMA or Moving Average for trend-based prediction.  
        """)
    with c4:
        st.markdown("""
        **🔍 Findings & Insights**  
        - Summarizes the conclusions drawn from the analysis.  
        - Highlights recommendations for improving engagement and fairness.  
        """)

    st.markdown("---")
    st.markdown("### 🧩 How It Works")
    st.markdown("""
    1. **Data Integration:** The dashboard reads cleaned R&R data (month, nominated to, given to, title, system version).  
    2. **Visualization:** Interactive charts reveal recognition trends by team, individual, and category.  
    3. **Comparison:** The system contrasts Old vs New models to identify shifts in engagement and fairness.  
    4. **Forecasting:** Predictive models estimate the number of coupons needed for future quarters.  
    """)

    st.markdown("---")
    st.markdown("### 🌟 Expected Outcomes")
    st.markdown("""
    - Improved understanding of recognition fairness and visibility.  
    - Data-driven insights to **enhance employee motivation and satisfaction.**  
    - Clear quarterly planning for **award distribution and budgeting.**  
    """)

    st.markdown("---")
    st.caption("Designed for the Capstone R&R Analysis — Bringing Clarity to Recognition Trends.")
