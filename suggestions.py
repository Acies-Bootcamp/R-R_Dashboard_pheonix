import streamlit as st

def show_suggestions_page():

    st.markdown("### 🔍 Findings & Insights")
    st.write("")  # spacing

    # ---------- CLEAN CARD STYLE ----------
    card_style = """
        <div style="
            background: #ffffff;
            padding: 18px 22px;
            border-radius: 14px;
            border-left: 6px solid #4A90E2;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 18px;
        ">
            <h4 style="margin-top: 0; margin-bottom: 8px; font-size: 20px; color: #2c3e50;">{title}</h4>
            <div style="font-size: 15px; color: #555; line-height: 1.55;">
                {content}
            </div>
        </div>
    """

    # ---------- CONTENT WITHOUT ANY HTML TAGS ----------
    spot_text = """
    In the earlier system, Spot Awards were highlighted in Kudu’s Corner, creating a strong emotional connection.

    In the new all-hands format, all recognitions are merged into a single placard, reducing visibility.

    Employees expressed that the emotional impact of Kudu’s Corner is missing.

    A dedicated section to highlight Spot Awards can help restore the impact.
    """

    awesome_text = """
    Many employees feel the Awesome Award lacks meaningful value in its current form.

    Suggestion: Rename it to something more meaningful, such as “Appreciation Award”.

    If keeping the name, apply stricter eligibility criteria so the award feels more significant.
    """

    single_award_text = """
    Data indicates some employees received only one award despite being part of larger teams.

    These individuals may be under-recognized in group-heavy award distributions.

    Recommendation: Highlight such contributors separately to ensure they receive the visibility they deserve.
    """

    # ---------- CONVERT NEWLINES TO <br> ----------
    spot_html = spot_text.replace("\n", "<br>")
    awesome_html = awesome_text.replace("\n", "<br>")
    single_html = single_award_text.replace("\n", "<br>")

    # ---------- DISPLAY CLEAN CARDS ----------
    st.markdown(card_style.format(
        title="1. Restore the Emotional Impact of Spot Awards",
        content=spot_html
    ), unsafe_allow_html=True)

    st.markdown(card_style.format(
        title="2. Improve the Value of the Awesome Award",
        content=awesome_html
    ), unsafe_allow_html=True)

    st.markdown(card_style.format(
        title="3. Improve Visibility for Single-Award Contributors",
        content=single_html
    ), unsafe_allow_html=True)
