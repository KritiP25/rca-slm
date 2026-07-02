# ==========================================================
# incident_input.py
# Step 1 — Incident Input page.
#
# User enters:
#   - Problem Description
#   - Business Impact
#   - Technical Investigation
#
# On clicking Generate RCA:
#   - Validates fields are not empty
#   - Calls backend /generate-rca
#   - Shows two-step loading indicator during inference
#   - Stores result in session state
#   - Navigates to rca_review page
# ==========================================================

import time
import streamlit as st

from utils.api_client import generate_rca
from components.progress_bar import render_progress_bar
from components.sidebar import render_sidebar


def render():
    """
    Renders the Incident Input page.
    All form state is stored in st.session_state so it
    persists when the user navigates back to this page.
    """
    render_sidebar()
    render_progress_bar()

    # ── Page Header ───────────────────────────────────────
    st.markdown("""
        <h1 style="font-size:28px; font-weight:700; color:#111827; margin-bottom:4px;">
            AI-Powered RCA Generator
        </h1>
        <p style="font-size:14px; color:#6B7280; margin-bottom:24px;">
            Describe your incident below. The AI will generate a structured
            Root Cause Analysis and CAPA plan.
        </p>
    """, unsafe_allow_html=True)

    # ── Backend connection check ──────────────────────────
    # Show warning if backend was previously unreachable
    if st.session_state.get("backend_ok") is False:
        st.warning(
            "⚠️ Backend is unreachable. "
            "Make sure Colab is running and the Cloudflare tunnel is active. "
            "Update `utils/config.py` with the new tunnel URL and restart Streamlit."
        )

    # ── Incident Input Form ───────────────────────────────
    with st.container():

        # Problem Description
        st.markdown("""
            <div style="margin-bottom:4px;">
                <span style="font-weight:600; font-size:14px; color:#111827;">
                    Problem Description
                </span><br>
                <span style="font-size:12px; color:#6B7280;">
                    What happened? When did it occur? Which systems were affected?
                </span>
            </div>
        """, unsafe_allow_html=True)

        problem_description = st.text_area(
            label="problem_description",
            label_visibility="collapsed",
            placeholder="At 02:14 UTC on June 28, 2026, the payment gateway began returning "
                        "HTTP 503 errors across all checkout flows...",
            value=st.session_state.get("problem_description", ""),
            height=120,
            key="input_problem_description",
        )

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # Business Impact
        st.markdown("""
            <div style="margin-bottom:4px;">
                <span style="font-weight:600; font-size:14px; color:#111827;">
                    Business Impact
                </span><br>
                <span style="font-size:12px; color:#6B7280;">
                    What was the customer, revenue, or operational impact?
                </span>
            </div>
        """, unsafe_allow_html=True)

        business_impact = st.text_area(
            label="business_impact",
            label_visibility="collapsed",
            placeholder="Revenue loss estimated at $2.3M. 847 merchant accounts unable "
                        "to process transactions. SLA breach triggered...",
            value=st.session_state.get("business_impact", ""),
            height=100,
            key="input_business_impact",
        )

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # Technical Investigation
        st.markdown("""
            <div style="margin-bottom:4px;">
                <span style="font-weight:600; font-size:14px; color:#111827;">
                    Technical Investigation
                </span><br>
                <span style="font-size:12px; color:#6B7280;">
                    What did you find? Logs, metrics, timeline, hypotheses.
                </span>
            </div>
        """, unsafe_allow_html=True)

        technical_investigation = st.text_area(
            label="technical_investigation",
            label_visibility="collapsed",
            placeholder="[14:32 UTC] HTTP 503 alerts fire on /api/v2/payments/process\n"
                        "[14:55 UTC] SSL certificate expiry confirmed on lb-payments-prod-01\n"
                        "[15:45 UTC] IAM permissions corrected, new certificate deployed\n"
                        "[18:55 UTC] Full service restoration confirmed",
            value=st.session_state.get("technical_investigation", ""),
            height=140,
            key="input_technical_investigation",
        )

    st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)

    # ── Generate RCA Button ───────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col2:
        generate_clicked = st.button(
            "✦ Generate RCA",
            type="primary",
            use_container_width=True,
        )

    # ── Validation + API Call ─────────────────────────────
    if generate_clicked:

        # Validate all fields are filled
        errors = []
        if not problem_description.strip():
            errors.append("Problem Description is required.")
        if not business_impact.strip():
            errors.append("Business Impact is required.")
        if not technical_investigation.strip():
            errors.append("Technical Investigation is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            # Save input to session state so it persists across pages
            st.session_state.problem_description    = problem_description.strip()
            st.session_state.business_impact        = business_impact.strip()
            st.session_state.technical_investigation = technical_investigation.strip()
            st.session_state.incident_submitted     = True

            # ── Two-step loading indicator ────────────────
            # Shown during the full pipeline:
            # SLM inference (~15s) + Groq expansion (~5s)
            status_placeholder = st.empty()

            with status_placeholder.container():
                st.markdown("""
                    <div style="
                        background:#F5F3FF;
                        border:1px solid #DDD6FE;
                        border-radius:8px;
                        padding:16px 20px;">
                        <div style="font-weight:600; color:#4F46E5; margin-bottom:8px;">
                            ⏳ Generating RCA...
                        </div>
                        <div style="font-size:13px; color:#6B7280;">
                            Step 1 of 2 — Fine-tuned SLM is analysing the incident...
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Call backend
            result = generate_rca(
                problem_description=st.session_state.problem_description,
                business_impact=st.session_state.business_impact,
                technical_investigation=st.session_state.technical_investigation,
            )

            # Update loading indicator to step 2
            if "error" not in result:
                with status_placeholder.container():
                    st.markdown("""
                        <div style="
                            background:#F5F3FF;
                            border:1px solid #DDD6FE;
                            border-radius:8px;
                            padding:16px 20px;">
                            <div style="font-weight:600; color:#4F46E5; margin-bottom:8px;">
                                ⏳ Expanding output...
                            </div>
                            <div style="font-size:13px; color:#6B7280;">
                                Step 2 of 2 — Groq Llama-3.3-70B expanding to enterprise prose...
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                time.sleep(0.5)  # Brief pause so user sees step 2

            status_placeholder.empty()

            # ── Handle result ─────────────────────────────
            if "error" in result:
                st.error(f"❌ Generation failed: {result['error']}")
                st.info(
                    "Make sure Colab is running and the Cloudflare tunnel is active. "
                    "Update `utils/config.py` with the current tunnel URL."
                )
            else:
                # Store result and flags in session state
                st.session_state.rca_output      = result
                st.session_state.rca_generated   = True
                st.session_state.groq_available  = result.get("groq_available", True)

                # Navigate to RCA review page
                st.session_state.page = "rca_review"
                st.rerun()

    # ── Footer ────────────────────────────────────────────
    st.markdown("""
        <div style="
            position:fixed; bottom:0; left:180px; right:0;
            padding:10px 24px;
            border-top:1px solid #E5E7EB;
            background:#FFFFFF;
            font-size:12px; color:#9CA3AF;
            text-align:center;">
            AI-Powered RCA Assistant · Academic Project ·
            <span style="color:#4F46E5; cursor:pointer;">Start New RCA</span>
        </div>
    """, unsafe_allow_html=True)