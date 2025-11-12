import streamlit as st
# from summary import show_summary
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
# from coupon_estimation import show_coupon_estimation

st.set_page_config(page_title="R&R Dashboard", layout="wide")

section = st.sidebar.radio("Go to Section", ["Summary Overview", "Recognition", "Award Analysis", "Coupon Estimation"])

def recognition_main():
    tab1, tab2 = st.tabs(["Team", "Individual"])
    with tab1:
        show_recognition_team_tab()  # The full team code provided
    with tab2:
        show_recognition_individual_tab()  # Separate function for individual analytics

if section == "Summary Overview":
    # show_summary()
    print()
elif section == "Recognition":
    recognition_main()

elif section == "Award Analysis":
    show_award_analysis()
    print()

elif section == "Coupon Estimation":
    # show_coupon_estimation()
    print()
