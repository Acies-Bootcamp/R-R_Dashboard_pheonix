import streamlit as st

def show_suggestions_page():

    st.markdown("### Findings & Recommendations")
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

    # ---------- TEXT BLOCKS (PLAIN, THEN CONVERT TO <br>) ----------

    # 1) Awesome Award – rename, criteria, open issues
    awesome_text = """
    • Consider renaming the “Awesome Award” to a stronger title such as “Appreciation Award” or “Impact Award”.
    • Restrict repeated nominations for the same person within short intervals.
    • Automatically flag vague or low-effort justifications for review before approval.
    • Create a separate Chat channel exclusively for Awesome Awards to make the other awards more visible\.
    • Many respondents reported that certificates shared in chat could not be opened — this needs a fix.
    """

    # 2) Spot Awards – restore emotional impact & visibility
    spot_text = """
    • Add a short “Recognition Recap” segment (about 3 minutes) in every Town Hall.
    • Use this segment to highlight the month’s Spot Award winners and key recognitions.
    • Prepare large-screen slides for Spot Awardees including:
      – Winner’s name and team with picture
      – A one-sentence achievement summary
    • This restores visibility and the emotional connection employees appreciated earlier.
    """

    # 3) Award templates & communication design
    templates_text = """
    • Redesign award certificate templates for better readability and a more premium feel.
    • Increase font sizes and improve hierarchy so the award title and recipient name stand out.
    • Certificates shared in chat should be easily openable and viewable in full size.
    • Include relevant context such as team name, mentor name, or a short citation.
    """

    # 4) Personalisation & weekly digest
    personalisation_text = """
    • Allow managers to add short personalised appreciation messages with each award.
    • Send a weekly R&R digest summarising recognitions: who was awarded and for what reason.
    """



    # ---------- CONVERT NEWLINES TO <br> ----------
    awesome_html = awesome_text.replace("\n", "<br>")
    spot_html = spot_text.replace("\n", "<br>")
    templates_html = templates_text.replace("\n", "<br>")
    personalisation_html = personalisation_text.replace("\n", "<br>")
    single_html = single_award_text.replace("\n", "<br>")

    # ---------- DISPLAY CARDS ----------
    st.markdown(card_style.format(
        title="1. Strengthen and Rename the Awesome Award",
        content=awesome_html
    ), unsafe_allow_html=True)

    st.markdown(card_style.format(
        title="2. Restore the Impact and Visibility of Spot Awards",
        content=spot_html
    ), unsafe_allow_html=True)

    st.markdown(card_style.format(
        title="3. Redesign Award Templates and Improve Accessibility",
        content=templates_html
    ), unsafe_allow_html=True)

    st.markdown(card_style.format(
        title="4. Increase Personalisation and Weekly Visibility",
        content=personalisation_html
    ), unsafe_allow_html=True)

