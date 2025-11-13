import streamlit as st
# from summary import show_summary
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
# from award_analysis import show_award_analysis
# from coupon_estimation import show_coupon_estimation

st.set_page_config(page_title="R&R Dashboard", layout="wide")

# Sidebar navigation
section = st.sidebar.radio(
    "Go to Section",
    ["Home","Overview", "Recognition", "Award Analysis", "Coupon Estimation","Findings/Insights"]
)

def recognition_main():
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()   # full team module
    with tab2:
        show_recognition_individual_tab()  # individual module

# Router
if section == "Home":
    print()
elif section == "Overview":
    st.title("Summary Overview")
    st.info("Summary page under development.")
    # show_summary()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    st.title("Award Analysis")
    st.info("Award Analysis module under development.")
    # show_award_analysis()

elif section == "Coupon Estimation":
    st.title("Coupon Estimation")
    st.info("Coupon Estimation module under development.")
    # show_coupon_estimation()
elif section =="Hypothesis/Insights":
    print()
