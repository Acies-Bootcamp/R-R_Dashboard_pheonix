import streamlit as st
import styles

# ---------------------------------------------------------
# 🧭 NAVIGATION BAR (Gapless + Clean Header Fix)
# ---------------------------------------------------------
def show_navbar():
    current_page = st.session_state.get("current_page", "Home")

    # Minimal CSS adjustments for layout. We intentionally avoid
    # overriding the navbar background and borders so the global
    # theme defined in ``styles.py`` remains visible.
    st.markdown("""
    <style>
    /* Remove default top padding and header */
    header, [data-testid="stHeader"] {
        margin-top: -3rem !important;
        padding-top: 0rem !important;
    }
    .main > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    /* Navbar wrapper positioning only. Background and colours are
       handled globally. */
    .navbar-wrapper {
        padding: 0.8rem 0.2rem 1.0rem 0.2rem;
        margin-top: -1rem !important;
        position: relative;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='navbar-wrapper'>", unsafe_allow_html=True)

    # 6 columns for 6 navigation items
    nav_cols = st.columns([1, 1, 1, 1, 1, 1])

    def nav_button(col, label, key, page):
        """Render a navigation button and update the current page state."""
        with col:
            btn_type = "primary" if current_page == page else "secondary"
            if st.button(label, key=key, use_container_width=True, type=btn_type):
                st.session_state.current_page = page
                st.rerun()

<<<<<<< HEAD
    nav_button(nav_cols[0], "🏠 Home", "nav_home", "Home")
    nav_button(nav_cols[1], "📊 Overview", "nav_overview", "Overview")
    nav_button(nav_cols[2], "🏅 Recognition", "nav_recognition", "Recognition")
    nav_button(nav_cols[3], "🏆 Award Analysis", "nav_award", "Award Analysis")
    nav_button(nav_cols[4], "📈 Coupon Estimation", "nav_coupon", "Coupon Estimation")
    nav_button(nav_cols[5], "🔍 Suggestions", "nav_findings", "Findings/Insights")
=======
    # Navigation buttons (no emojis)
    nav_button(nav_cols[0], "Home", "nav_home", "Home")
    nav_button(nav_cols[1], "Overview", "nav_overview", "Overview")
    nav_button(nav_cols[2], "Recognition", "nav_recognition", "Recognition")
    nav_button(nav_cols[3], "Award Analysis", "nav_award", "Award Analysis")
    nav_button(nav_cols[4], "Coupon Estimation", "nav_coupon", "Coupon Estimation")
    nav_button(nav_cols[5], "Recommendations", "nav_recommendations", "Recommendations")
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 🏡 HOME PAGE CONTENT
# ---------------------------------------------------------
def show_home_page():
    # Apply global styling at the beginning of the home page
    theme = st.session_state.get("theme", "White")
    styles.apply_styles(theme=theme)

    # -----------------------------------
    # PAGE CONTENT (Starts directly)
    # -----------------------------------
    st.markdown("""
    Welcome to the **Rewards & Recognition (R&R) Dashboard** — a comprehensive platform designed to analyze and visualize how recognition flows across teams and individuals within the organization.  
    This dashboard evaluates the transition from the *Old Mentor-Based System* to the *New Peer-to-Peer Model* launched in June 2025.
    """)

    st.markdown("---")
    st.markdown("### Purpose")
    st.markdown("""
    - Understand the **effectiveness and fairness** of the new recognition process.  
    - Identify **team and individual performance trends**.  
    - Analyze **award distribution** across departments.  
    - Forecast future **coupon requirements**.  
    """)

    st.markdown("---")
    st.markdown("### Core Modules")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Recognition Module**  
        - Team and individual level breakdown  
        - Participation and nomination trends  
        """)
    with col2:
        st.markdown("""
        **Award Analysis Module**  
        - Title frequency  
        - Category distribution  
        """)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""
        **Coupon Forecasting Module**  
        - SARIMA and Moving Average models  
        """)
    with col4:
        st.markdown("""
<<<<<<< HEAD
        **🔍 Suggestions**  
        - Recommendations & fairness analysis  
=======
        **Insights Module**  
        - Recommendations and fairness analysis  
>>>>>>> 16da823da55549cc448a5ce4535cda6b94d321d3
        """)

    st.markdown("---")
    st.caption("Designed for the Capstone R&R Analysis — Bringing clarity to recognition trends.")
