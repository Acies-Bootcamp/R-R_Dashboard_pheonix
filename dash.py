import streamlit as st
from summary_overview import show_summary_overview
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
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
    show_summary_overview()

elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    show_award_analysis()
    print()
    st.title("Award Analysis")
    show_award_analysis()

elif section == "Coupon Estimation":
    st.title("Coupon Estimation")
    # show_coupon_estimation()
elif section =="Hypothesis/Insights":
    print()
