import streamlit as st
# from summary import show_summary
from recognition import show_recognition_team_tab
# from award_analysis import show_award_analysis
# from coupon_estimation import show_coupon_estimation

st.set_page_config(page_title="R&R Dashboard", layout="wide")

section = st.sidebar.radio("Go to Section", ["Summary Overview", "Recognition", "Award Analysis", "Coupon Estimation"])

if section == "Summary Overview":
    # show_summary()
    print()
elif section == "Recognition":
    show_recognition_team_tab()

elif section == "Award Analysis":
    # show_award_analysis()
    print()

elif section == "Coupon Estimation":
    # show_coupon_estimation()
    print()
