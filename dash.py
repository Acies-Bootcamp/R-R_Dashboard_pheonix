import streamlit as st

# Must be first Streamlit command
st.set_page_config(page_title="R&R Dashboard", layout="wide")

# Load CSS
from utils import load_css
load_css()

# Import pages
from summary_overview import show_summary_overview
from home import show_home_page
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
from coupoun_estimation import show_coupon_estimation


# ---------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------
with st.sidebar:
    st.markdown("### Go to Section")
    section = st.radio(
        "",
        ["Home", "Overview", "Recognition", "Award Analysis", "Coupon Estimation", "Findings/Insights"]
    )

# ---------------------------------------------
# RECOGNITION PAGE (Tabs)
# ---------------------------------------------
def recognition_main():
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()
    with tab2:
        show_recognition_individual_tab()


# ---------------------------------------------
# ROUTER
# ---------------------------------------------
if section == "Home":
    show_home_page()

elif section == "Overview":
    show_summary_overview()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    show_award_analysis()

elif section == "Coupon Estimation":
    show_coupon_estimation()

elif section == "Findings/Insights":
    st.markdown("<h2>🔍 Findings & Insights</h2>", unsafe_allow_html=True)
    st.info("Add your insights here.")
