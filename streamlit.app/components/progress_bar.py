# ==========================================================
# progress_bar.py
# Top horizontal 4-step progress indicator shown on every page.
# Matches the Figma design — numbered circles connected by lines,
# with completed steps green, active step purple, future steps gray.
# ==========================================================

import streamlit as st

# The 4 top-level stages shown in the progress bar
# These are broader than the sidebar workflow steps
STAGES = [
    (1, "Incident Input"),
    (2, "RCA Review"),
    (3, "CAPA Review"),
    (4, "Report"),
]

# Map page names to stage number (1-based)
PAGE_TO_STAGE = {
    "incident_input": 1,
    "rca_review":     2,
    "capa_review":    3,
    "report":         4,
}


def render_progress_bar():
    """
    Renders the top horizontal stage progress bar.
    Shows 4 stages connected by lines.
    Completed = green circle with checkmark.
    Active = purple circle with number.
    Future = gray circle with number.
    """
    current_page  = st.session_state.get("page", "incident_input")
    current_stage = PAGE_TO_STAGE.get(current_page, 1)

    # Build HTML for the progress bar — pure HTML/CSS to match
    # Figma design precisely since Streamlit has no native stepper
    items_html = ""
    for i, (num, label) in enumerate(STAGES):
        is_complete = num < current_stage
        is_active   = num == current_stage

        if is_complete:
            circle_bg    = "#16A34A"
            circle_color = "#FFFFFF"
            circle_text  = "✓"
            label_color  = "#16A34A"
            label_weight = "500"
        elif is_active:
            circle_bg    = "#4F46E5"
            circle_color = "#FFFFFF"
            circle_text  = str(num)
            label_color  = "#4F46E5"
            label_weight = "600"
        else:
            circle_bg    = "#FFFFFF"
            circle_color = "#9CA3AF"
            circle_text  = str(num)
            label_color  = "#9CA3AF"
            label_weight = "400"

        # Connector line between stages (not after last)
        connector = ""
        if i < len(STAGES) - 1:
            line_color = "#16A34A" if is_complete else "#E5E7EB"
            connector = f"""
                <div style="
                    flex:1; height:2px;
                    background:{line_color};
                    margin:0 8px;
                    margin-top:-16px;">
                </div>
            """

        items_html += f"""
            <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
                <div style="
                    width:28px; height:28px;
                    border-radius:50%;
                    background:{circle_bg};
                    border: 2px solid {circle_bg if is_active or is_complete else '#E5E7EB'};
                    display:flex; align-items:center; justify-content:center;
                    font-size:12px; font-weight:600;
                    color:{circle_color};">
                    {circle_text}
                </div>
                <div style="
                    font-size:12px;
                    color:{label_color};
                    font-weight:{label_weight};
                    white-space:nowrap;">
                    {label}
                </div>
            </div>
            {connector}
        """

    st.markdown(f"""
        <div style="
            display:flex;
            align-items:flex-start;
            justify-content:center;
            padding:12px 40px 8px 40px;
            background:#FFFFFF;
            border-bottom:1px solid #E5E7EB;
            margin-bottom:24px;">
            {items_html}
        </div>
    """, unsafe_allow_html=True)