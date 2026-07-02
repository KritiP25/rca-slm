# ==========================================================
# sidebar.py
# Left sidebar component rendered on every page.
#
# Contains:
#   - App logo and title
#   - Workflow progress bar + step list
#   - Start New RCA button
#   - About section (updated to reflect actual tech stack)
#   - Backend connection status indicator
# ==========================================================

import streamlit as st


# Workflow steps in order — used to compute progress % and
# highlight the current active step in the sidebar list
WORKFLOW_STEPS = [
    "Incident Input",
    "RCA Generated",
    "RCA Review",
    "CAPA Generation",
    "CAPA Review",
    "Report Generation",
]

# Map page names to their workflow step index (0-based)
# Used to determine which step is currently active
PAGE_TO_STEP = {
    "incident_input":   0,
    "rca_review":       2,
    "capa_review":      4,
    "report":           5,
}


def render_sidebar():
    """
    Renders the full left sidebar.
    Reads current page from st.session_state.page to highlight
    the active workflow step and compute progress percentage.
    """
    with st.sidebar:

        # ── Logo + Title ──────────────────────────────────
        st.markdown("""
            <div style="display:flex; align-items:center; gap:10px; padding:8px 0 16px 0;">
                <div style="
                    background:#4F46E5;
                    border-radius:8px;
                    width:36px; height:36px;
                    display:flex; align-items:center; justify-content:center;
                    font-size:18px;">✦</div>
                <div>
                    <div style="font-weight:600; font-size:15px; color:#111827;">RCA Assistant</div>
                    <div style="font-size:12px; color:#6B7280;">AI-Powered</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Workflow Progress ─────────────────────────────
        current_page = st.session_state.get("page", "incident_input")
        current_step = PAGE_TO_STEP.get(current_page, 0)
        progress_pct = int((current_step / (len(WORKFLOW_STEPS) - 1)) * 100)

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                "<div style='font-size:11px; font-weight:600; "
                "color:#6B7280; letter-spacing:0.05em;'>WORKFLOW</div>",
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"<div style='font-size:11px; font-weight:600; "
                f"color:#4F46E5; text-align:right;'>{progress_pct}%</div>",
                unsafe_allow_html=True
            )

        # Progress bar
        st.markdown(f"""
            <div style="
                height:4px; background:#E5E7EB; border-radius:2px; margin:4px 0 12px 0;">
                <div style="
                    width:{progress_pct}%;
                    height:4px;
                    background:#4F46E5;
                    border-radius:2px;
                    transition:width 0.3s;">
                </div>
            </div>
        """, unsafe_allow_html=True)

        # ── Workflow Steps List ───────────────────────────
        session = st.session_state

        # Determine which steps are complete based on session state
        steps_complete = {
            0: session.get("incident_submitted", False),
            1: session.get("rca_generated", False),
            2: session.get("rca_approved", False),
            3: session.get("capa_generated", False),
            4: session.get("capa_approved", False),
            5: session.get("report_generated", False),
        }

        for i, step_name in enumerate(WORKFLOW_STEPS):
            is_active   = (i == current_step)
            is_complete = steps_complete.get(i, False)
            is_future   = (i > current_step) and not is_complete

            if is_complete:
                icon  = "✅"
                color = "#16A34A"
                weight = "500"
            elif is_active:
                icon  = "🔵"
                color = "#4F46E5"
                weight = "600"
            else:
                icon  = "⚪"
                color = "#9CA3AF"
                weight = "400"

            st.markdown(f"""
                <div style="
                    display:flex; align-items:center; gap:8px;
                    padding:5px 0; font-size:13px;
                    color:{color}; font-weight:{weight};">
                    <span style="font-size:10px;">{icon}</span>
                    {step_name}
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin:8px 0;'></div>", unsafe_allow_html=True)

        # ── Start New RCA Button ──────────────────────────
        if st.button("↺  Start New RCA", use_container_width=True):
            # Clear all session state except the page key
            # This resets the entire workflow from scratch
            keys_to_clear = [
                "incident_submitted", "rca_generated", "rca_approved",
                "capa_generated", "capa_approved", "report_generated",
                "incident_data", "rca_output", "capa_output",
                "page", "groq_available",
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "incident_input"
            st.rerun()

        st.divider()

        # ── About Section ─────────────────────────────────
        with st.expander("ⓘ  About", expanded=False):
            st.markdown("""
                **AI-Powered RCA & CAPA Generator**

                This tool automates Root Cause Analysis reports and
                Corrective & Preventive Action plans from incident
                descriptions using fine-tuned language models.

                **How it works**

                1. Enter incident details — problem description,
                   business impact, technical findings.
                2. Fine-tuned **Qwen2.5-3B** (LoRA) generates a
                   structured Five Why analysis and root cause.
                3. **Groq Llama-3.3-70B** expands the output to
                   verbose enterprise prose.
                4. Automated validation checks structure and
                   semantic consistency.
                5. Review, provide feedback, or regenerate.
                6. Generate the final report as DOCX and PDF.

                **Tech Stack**
                - SLM: Qwen2.5-3B-Instruct + LoRA (Unsloth)
                - Expansion: Groq Llama-3.3-70B-Versatile
                - Backend: FastAPI (Google Colab)
                - Frontend: Streamlit

                ---
                *Academic capstone project.*
            """)

        # ── Backend Status ────────────────────────────────
        # Small indicator at the very bottom of the sidebar
        # showing whether the backend is reachable
        backend_ok = st.session_state.get("backend_ok", None)
        if backend_ok is True:
            st.markdown(
                "<div style='font-size:11px; color:#16A34A; margin-top:8px;'>"
                "● Backend connected</div>",
                unsafe_allow_html=True
            )
        elif backend_ok is False:
            st.markdown(
                "<div style='font-size:11px; color:#DC2626; margin-top:8px;'>"
                "● Backend unreachable — check Colab</div>",
                unsafe_allow_html=True
            )