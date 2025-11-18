import streamlit as st
from home import show_home_page, show_navbar
import styles
from summary_overview import show_rr_dashboard
from reco_team import show_recognition_team_tab
from reco_individual import show_recognition_individual_tab
from award_analysis import show_award_analysis
from coupoun_estimation import show_coupon_estimation
from suggestions import show_suggestions_page
# from summary import show_summary  # optional

# ------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------
st.set_page_config(
    page_title="R&R Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Determine the chosen theme from session state or default to White.
selected_theme = st.session_state.get("theme", "White")

# Apply global styles based on the selected theme
styles.apply_styles(theme=selected_theme)

# Display a custom spinner in the centre of the screen while the app loads.
styles.show_spinner(1.0)

# Hide Streamlit sidebar + default header
st.markdown(
    """
<style>
    section[data-testid="stSidebar"] {display: none !important;}
    .stApp > header {display: none !important;}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------
# SESSION STATE — Current Page
# ------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

section = st.session_state.current_page

# ------------------------------------------------------
# ACIES LOGO + PAGE TITLES + THREE-DOT MENU
# ------------------------------------------------------
logo_col, title_col, menu_col = st.columns([1, 3, 1])

# LOGO — Always visible
with logo_col:
    st.image("acieslogo.png", width=140)

# TITLES (Different for each page) — no emojis
with title_col:
    if section == "Home":
        st.markdown(
            """
        <div style='text-align: center; margin-top: 0.5rem;'>
            <h1 style='font-size: 42px; font-weight: 700; margin-bottom: 0px;'>
                Rewards & Recognition Dashboard
            </h1>
            <p style='color: #666; margin-top: -5px; font-size: 0.9rem;'>
                Developed as part of the Capstone Project • November 2025
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    elif section == "Overview":
        st.markdown(
            "<h2 style='text-align:center; margin-top:1rem;'>Overview Dashboard</h2>",
            unsafe_allow_html=True,
        )

    elif section == "Recognition":
        st.markdown(
            "<h2 style='text-align:center; margin-top:1rem;'>Recognition Analysis</h2>",
            unsafe_allow_html=True,
        )

    elif section == "Award Analysis":
        st.markdown(
            "<h2 style='text-align:center; margin-top:1rem;'>Award Analysis</h2>",
            unsafe_allow_html=True,
        )

    elif section == "Coupon Estimation":
        st.markdown(
            "<h2 style='text-align:center; margin-top:1rem;'>Coupon Estimation</h2>",
            unsafe_allow_html=True,
        )

    elif section == "Recommendations":
        st.markdown(
            "<h2 style='text-align:center; margin-top:1rem;'>Recommendations</h2>",
            unsafe_allow_html=True,
        )

# THREE-DOT MENU (⋮) with Rerun + Clear Cache
with menu_col:
    st.markdown(
        """
        <style>
        .three-dot-btn {
            font-size: 28px;
            font-weight: 600;
            cursor: pointer;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid #0D3C66;
            background: rgba(255,255,255,0.3);
        }
        .three-dot-btn:hover {
            background: rgba(255,255,255,0.45);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.popover("⋮", use_container_width=False):
        st.markdown("### Actions")

        # Row-wise buttons
        if st.button("Rerun App", use_container_width=True, type="primary"):
            st.rerun()

        if st.button("Clear Cache & Reload", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

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

elif section == "Recommendations":
    show_suggestions_page()

# ------------------------------------------------------
# AUTO SCROLL TO TOP on every navigation
# ------------------------------------------------------
st.markdown(
    """
<script>
    window.parent.document
        .querySelector('section.main')
        ?.scrollTo(0, 0);
</script>
""",
    unsafe_allow_html=True,
)
