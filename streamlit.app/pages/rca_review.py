# ==========================================================
# rca_review.py
# Step 2 — RCA Review page.
#
# Displays the AI-generated Five Why Analysis and Root Cause
# Summary for human review. User can:
#   - Approve RCA → navigate to CAPA generation
#   - Edit manually → fields become editable text areas
#   - Provide feedback + Regenerate → calls /regenerate-rca
#
# Also shows:
#   - Groq fallback banner if expansion was unavailable
#   - AI disclaimer
#   - Validation status
# ==========================================================

import streamlit as st
import time

from utils.api_client import regenerate_rca
from components.progress_bar import render_progress_bar
from components.sidebar import render_sidebar


def _render_validation(validation: dict):
    """
    Renders the validation status card.
    Shows rule-based and structure check results.
    Lists any specific issues if validation failed.
    """
    passed = validation.get("passed", True)
    issues = validation.get("issues", [])

    if passed:
        st.markdown("""
            <div style="
                background:#F0FDF4;
                border:1px solid #BBF7D0;
                border-radius:8px;
                padding:12px 16px;
                margin:16px 0;">
                <div style="font-size:11px; font-weight:600;
                    color:#6B7280; letter-spacing:0.05em; margin-bottom:6px;">
                    FACT VALIDATION
                </div>
                <div style="font-size:13px; color:#16A34A;">
                    ✅ Rule-Based Validation Passed
                </div>
                <div style="font-size:13px; color:#16A34A;">
                    ✅ Structure Valid
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        issues_html = "".join([
            f"<div style='font-size:12px; color:#DC2626; margin-top:4px;'>"
            f"• {issue.get('issue', '')}</div>"
            for issue in issues
        ])
        st.markdown(f"""
            <div style="
                background:#FEF2F2;
                border:1px solid #FECACA;
                border-radius:8px;
                padding:12px 16px;
                margin:16px 0;">
                <div style="font-size:11px; font-weight:600;
                    color:#6B7280; letter-spacing:0.05em; margin-bottom:6px;">
                    FACT VALIDATION
                </div>
                <div style="font-size:13px; color:#DC2626;">
                    ❌ Validation issues found — review before approving
                </div>
                {issues_html}
            </div>
        """, unsafe_allow_html=True)


def _render_five_why(five_why: list, edit_mode: bool) -> list:
    """
    Renders the Five Why Analysis section.
    In view mode: clean numbered cards with question + answer.
    In edit mode: text areas for question and answer per item.

    Returns the (possibly edited) five_why list.
    """
    st.markdown("""
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:10px;
            padding:20px;
            margin-bottom:16px;">
            <div style="font-weight:600; font-size:15px;
                color:#111827; margin-bottom:16px;">
                Five Why Analysis
            </div>
    """, unsafe_allow_html=True)

    updated_five_why = []

    for i, item in enumerate(five_why):
        question = item.get("question", "")
        answer   = item.get("answer", "")

        if edit_mode:
            st.markdown(
                f"<div style='font-size:12px; font-weight:600; "
                f"color:#4F46E5; margin-bottom:2px;'>Why {i+1}</div>",
                unsafe_allow_html=True
            )
            new_q = st.text_input(
                f"Question {i+1}",
                value=question,
                key=f"rca_edit_q_{i}",
                label_visibility="collapsed",
            )
            new_a = st.text_area(
                f"Answer {i+1}",
                value=answer,
                key=f"rca_edit_a_{i}",
                height=80,
                label_visibility="collapsed",
            )
            updated_five_why.append({"question": new_q, "answer": new_a})
            if i < len(five_why) - 1:
                st.markdown(
                    "<hr style='border:none; border-top:1px solid #F3F4F6; margin:8px 0;'>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown(f"""
                <div style="display:flex; gap:12px; margin-bottom:16px;">
                    <div style="
                        background:#4F46E5;
                        color:#FFFFFF;
                        border-radius:50%;
                        width:26px; height:26px; min-width:26px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:12px; font-weight:600;">
                        {i+1}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:13px;
                            color:#111827; margin-bottom:4px;">
                            {question}
                        </div>
                        <div style="font-size:13px; color:#374151;
                            line-height:1.6;">
                            {answer}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            updated_five_why.append(item)

    st.markdown("</div>", unsafe_allow_html=True)
    return updated_five_why


def _render_root_cause(root_cause: dict, edit_mode: bool) -> dict:
    """
    Renders the Root Cause Summary section.
    In view mode: statement with left border + category badge.
    In edit mode: editable text areas.

    Returns the (possibly edited) root_cause dict.
    """
    statement = root_cause.get("statement", "")
    category  = root_cause.get("root_cause_category", "")

    st.markdown("""
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:10px;
            padding:20px;
            margin-bottom:16px;">
            <div style="font-weight:600; font-size:15px;
                color:#111827; margin-bottom:16px;">
                Root Cause
            </div>
    """, unsafe_allow_html=True)

    if edit_mode:
        new_statement = st.text_area(
            "Root cause statement",
            value=statement,
            height=120,
            key="rca_edit_statement",
            label_visibility="collapsed",
        )
        new_category = st.text_input(
            "Root cause category",
            value=category,
            key="rca_edit_category",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return {"statement": new_statement, "root_cause_category": new_category}
    else:
        st.markdown(f"""
            <div style="
                border-left:3px solid #4F46E5;
                padding-left:16px;
                margin-bottom:12px;">
                <div style="font-size:13px; color:#374151; line-height:1.7;">
                    {statement}
                </div>
            </div>
            <div style="margin-top:8px;">
                <span style="
                    background:#EEF2FF;
                    color:#4F46E5;
                    font-size:11px;
                    font-weight:500;
                    padding:2px 8px;
                    border-radius:4px;">
                    {category}
                </span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return root_cause


def render():
    """
    Renders the RCA Review page.
    Guards against direct access if RCA has not been generated yet.
    """
    render_sidebar()
    render_progress_bar()

    # ── Guard — redirect if RCA not generated ─────────────
    if not st.session_state.get("rca_generated"):
        st.warning("No RCA generated yet. Please complete the incident input first.")
        if st.button("← Go to Incident Input"):
            st.session_state.page = "incident_input"
            st.rerun()
        return

    rca_output = st.session_state.get("rca_output", {})
    five_why   = rca_output.get("five_why_analysis", [])
    root_cause = rca_output.get("root_cause_summary", {})
    validation = rca_output.get("validation", {"passed": True, "issues": []})

    # ── Page Header ───────────────────────────────────────
    st.markdown("""
        <h1 style="font-size:26px; font-weight:700; color:#111827; margin-bottom:4px;">
            RCA Review
        </h1>
        <p style="font-size:14px; color:#6B7280; margin-bottom:20px;">
            Review the AI-generated analysis. Approve, edit, or regenerate.
        </p>
    """, unsafe_allow_html=True)

    # ── Groq fallback banner ──────────────────────────────
    if not st.session_state.get("groq_available", True):
        st.warning(
            "⚠️ AI expansion temporarily unavailable — output may be less detailed "
            "than usual. You can edit content manually before approving."
        )

    # ── AI disclaimer ─────────────────────────────────────
    st.markdown("""
        <div style="
            font-size:12px; color:#9CA3AF;
            margin-bottom:16px;
            padding:8px 12px;
            background:#F9FAFB;
            border-radius:6px;
            border:1px solid #F3F4F6;">
            🤖 AI-generated content — verify all technical details before approving.
        </div>
    """, unsafe_allow_html=True)

    # ── Edit mode toggle ──────────────────────────────────
    edit_mode = st.session_state.get("rca_edit_mode", False)

    # ── Five Why + Root Cause ─────────────────────────────
    updated_five_why  = _render_five_why(five_why, edit_mode)
    updated_root_cause = _render_root_cause(root_cause, edit_mode)

    # ── Validation ────────────────────────────────────────
    _render_validation(validation)

    # ── Feedback ──────────────────────────────────────────
    st.markdown("""
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:10px;
            padding:20px;
            margin-bottom:20px;">
            <div style="font-weight:600; font-size:14px; color:#111827; margin-bottom:4px;">
                Feedback
            </div>
            <div style="font-size:12px; color:#6B7280; margin-bottom:8px;">
                Optional — suggest corrections before regenerating.
            </div>
    """, unsafe_allow_html=True)

    feedback = st.text_area(
        label="feedback",
        label_visibility="collapsed",
        placeholder="e.g. The root cause should focus more on the IAM misconfiguration "
                    "rather than the certificate expiry...",
        height=100,
        key="rca_feedback",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Action Buttons ────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1.5])

    with col1:
        approve_clicked = st.button(
            "👍 Approve RCA",
            type="primary",
            use_container_width=True,
            key="approve_rca_btn",
        )

    with col2:
        edit_clicked = st.button(
            "✏️ Edit",
            use_container_width=True,
            key="edit_rca_btn",
        )

    with col3:
        regen_clicked = st.button(
            "↺ Regenerate RCA",
            use_container_width=True,
            key="regen_rca_btn",
        )

    # ── Button Logic ──────────────────────────────────────

    if approve_clicked:
        # Save edited content if in edit mode
        if edit_mode:
            st.session_state.rca_output["five_why_analysis"]  = updated_five_why
            st.session_state.rca_output["root_cause_summary"] = updated_root_cause

        # Mark RCA as approved and navigate to CAPA generation
        st.session_state.rca_approved  = True
        st.session_state.rca_edit_mode = False
        st.session_state.page          = "capa_review"

        # Trigger CAPA generation immediately on navigation
        st.session_state.trigger_capa_generation = True
        st.rerun()

    if edit_clicked:
        # Toggle edit mode
        st.session_state.rca_edit_mode = not edit_mode
        st.rerun()

    if regen_clicked:
        # Build incident dict for regeneration prompt
        original_incident = {
            "problem_description":    st.session_state.get("problem_description", ""),
            "business_impact":        st.session_state.get("business_impact", ""),
            "technical_investigation": st.session_state.get("technical_investigation", ""),
        }

        # Show loading indicator
        status = st.empty()
        with status.container():
            st.markdown("""
                <div style="
                    background:#F5F3FF; border:1px solid #DDD6FE;
                    border-radius:8px; padding:16px 20px;">
                    <div style="font-weight:600; color:#4F46E5; margin-bottom:6px;">
                        ⏳ Regenerating RCA...
                    </div>
                    <div style="font-size:13px; color:#6B7280;">
                        Step 1 of 2 — SLM regenerating with your feedback...
                    </div>
                </div>
            """, unsafe_allow_html=True)

        result = regenerate_rca(
            original_incident=original_incident,
            previous_rca={
                "five_why_analysis":  five_why,
                "root_cause_summary": root_cause,
            },
            user_feedback=feedback or "Please improve the analysis.",
        )

        if "error" not in result:
            with status.container():
                st.markdown("""
                    <div style="
                        background:#F5F3FF; border:1px solid #DDD6FE;
                        border-radius:8px; padding:16px 20px;">
                        <div style="font-weight:600; color:#4F46E5; margin-bottom:6px;">
                            ⏳ Expanding output...
                        </div>
                        <div style="font-size:13px; color:#6B7280;">
                            Step 2 of 2 — Groq expanding to enterprise prose...
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            time.sleep(0.5)

        status.empty()

        if "error" in result:
            st.error(f"❌ Regeneration failed: {result['error']}")
        else:
            st.session_state.rca_output     = result
            st.session_state.groq_available = result.get("groq_available", True)
            st.session_state.rca_edit_mode  = False
            st.success("✅ RCA regenerated successfully.")
            st.rerun()

    # ── Back navigation ───────────────────────────────────
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Incident Input"):
        st.session_state.page = "incident_input"
        st.rerun()