import streamlit as st
from summary_overview import show_rr_dashboard
from home import show_home_page
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
from coupoun_estimation import show_coupon_estimation



# Sidebar navigation
section = st.sidebar.radio(
    "Go to Section",
    ["Home", "Overview", "Recognition", "Award Analysis", "Coupon Estimation", "Findings/Insights"]
)

def recognition_main():
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()
    with tab2:
        show_recognition_individual_tab()

# Router
if section == "Home":
    show_home_page()

elif section == "Overview":
    st.title("Summary Overview")
    show_rr_dashboard()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    st.title("Award Analysis")
    show_award_analysis()

elif section == "Coupon Estimation":
    show_coupon_estimation()

elif section == "Findings/Insights":
    st.title("Findings / Insights")
    st.info("Add your final insights and interpretations here.")
