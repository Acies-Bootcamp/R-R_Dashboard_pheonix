import streamlit as st
from home import show_home_page
from summary_overview import show_rr_dashboard
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
from coupoun_estimation import show_coupon_estimation
# from summary import show_summary  # optional future import

# ----------- Page Config -----------
st.set_page_config(
    page_title="R&R Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ----------- Sidebar Navigation -----------
section = st.sidebar.radio(
    "Go to Section",
    [
        "Home",
        "Overview",
        "Recognition",
        "Award Analysis",
        "Coupon Estimation",
        "Findings/Insights"
    ],
    index=0
)

# ----------- Recognition Tabs -----------
def recognition_main():
    st.title("Recognition Analysis")
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()
    with tab2:
        show_recognition_individual_tab()

# ----------- Router -----------
if section == "Home":
    show_home_page()

elif section == "Overview":
    st.title("R&R Effectiveness Dashboard — Form responses Only")
    show_rr_dashboard()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    show_award_analysis()

elif section == "Coupon Estimation":
    st.caption("💡 Coupon Estimation logic and parameters coming soon.")
    show_coupon_estimation()

elif section == "Findings/Insights":
    st.title("Findings / Insights")
    st.info("Add final insights, interpretations, or visual summaries here.")
