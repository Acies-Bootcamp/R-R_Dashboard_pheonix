import streamlit as st
from home import show_home_page, show_navbar
from summary_overview import show_rr_dashboard
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
from coupoun_estimation import show_coupon_estimation
from suggestions import show_suggestions_page

# ------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------
st.set_page_config(
    page_title="R&R Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit sidebar + default header
st.markdown("""
<style>
    section[data-testid="stSidebar"] {display: none !important;}
    .stApp > header {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# SESSION STATE — Current Page
# ------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

section = st.session_state.current_page

# ------------------------------------------------------
# ⭐ ACIES LOGO + PAGE TITLES
# ------------------------------------------------------
logo_col, title_col, empty_col = st.columns([1, 3, 1])

# LOGO — Always visible
with logo_col:
    st.image("acieslogo.png", width=140)

# TITLES (Different for each page)
with title_col:
    if section == "Home":
        st.markdown("""
        <div style='text-align: center; margin-top: 0.5rem;'>
            <h1 style='font-size: 42px; font-weight: 700; margin-bottom: 0px;'>
                🏆 Rewards & Recognition Dashboard
            </h1>
            <p style='color: #666; margin-top: -5px; font-size: 0.9rem;'>
                Developed as part of the Capstone Project • November 2025
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif section == "Overview":
        st.markdown("<h2 style='text-align:center; margin-top:1rem;'>📊 Overview Dashboard</h2>", unsafe_allow_html=True)

    elif section == "Recognition":
        st.markdown("<h2 style='text-align:center; margin-top:1rem;'>🏅 Recognition Analysis</h2>", unsafe_allow_html=True)

    elif section == "Award Analysis":
        st.markdown("<h2 style='text-align:center; margin-top:1rem;'>🏆 Award Analysis</h2>", unsafe_allow_html=True)

    elif section == "Coupon Estimation":
        st.markdown("<h2 style='text-align:center; margin-top:1rem;'>📈 Coupon Estimation</h2>", unsafe_allow_html=True)

    elif section == "Findings/Insights":
        st.markdown("<h2 style='text-align:center; margin-top:1rem;'>🔍 Findings & Insights</h2>", unsafe_allow_html=True)

# ------------------------------------------------------
# NAVBAR — Always below logo/title
# ------------------------------------------------------
show_navbar()

# ------------------------------------------------------
# RECOGNITION PAGE TABS
# ------------------------------------------------------
def recognition_main():
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()
    with tab2:
        show_recognition_individual_tab()

# ------------------------------------------------------
# PAGE ROUTER
# ------------------------------------------------------
if section == "Home":
    show_home_page()

elif section == "Overview":
    show_rr_dashboard()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    show_award_analysis()

elif section == "Coupon Estimation":
    show_coupon_estimation()

elif section == "Findings/Insights":
    show_suggestions_page()   # ✅ Updated

# ------------------------------------------------------
# AUTO SCROLL TO TOP on every navigation
# ------------------------------------------------------
st.markdown("""
<script>
    window.parent.document.querySelector('section.main').scrollTo(0, 0);
</script>
""", unsafe_allow_html=True)
