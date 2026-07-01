# ==========================================================
# rca_service.py
# Orchestrates the full RCA generation pipeline:
#   1. Build prompt (task-prefixed, matching training format)
#   2. Run SLM inference
#   3. Parse JSON output
#   4. Expand with Groq to verbose enterprise prose
#   5. Return structured dict + groq status flags
#
# Groq expansion is optional — if unavailable, raw SLM
# output is returned and groq_available=False is set so
# the frontend can show the appropriate banner.
# ==========================================================

import json
import logging
import os
from typing import Any, Dict, Tuple

from src.reasoning.inference import generate_output
from src.reasoning.prompts import (
    build_rca_prompt,
    build_rca_regeneration_prompt,
)
from src.reasoning.groq_expansion import expand_with_groq

logger = logging.getLogger(__name__)

# Required top-level keys in a valid RCA JSON output
REQUIRED_RCA_KEYS = {"five_why_analysis", "root_cause_summary"}


def _parse_rca_output(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Attempts to parse the model's raw text output as JSON.
    Strips issue_summary if the model still produces it.

    Returns:
        (parsed_dict, success_bool)
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"RCA JSON parse failed: {e} | raw: {raw_text[:300]}")
        return {}, False

    # Remove issue_summary if model still outputs it
    data.pop("issue_summary", None)

    missing = REQUIRED_RCA_KEYS - set(data.keys())
    if missing:
        logger.warning(f"RCA output missing required keys: {missing}")
        return data, False

    five_why = data.get("five_why_analysis", [])
    if not isinstance(five_why, list) or len(five_why) == 0:
        logger.warning("five_why_analysis is empty or not a list")
        return data, False

    rcs = data.get("root_cause_summary", {})
    if not rcs.get("statement") or not rcs.get("root_cause_category"):
        logger.warning("root_cause_summary missing statement or root_cause_category")
        return data, False

    return data, True


def _build_incident_text(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
) -> str:
    """
    Combines incident fields into a single string.
    Used as the source-of-truth for Groq hallucination detection.
    """
    return (
        f"Problem Description:\n{problem_description}\n\n"
        f"Business Impact:\n{business_impact}\n\n"
        f"Technical Investigation:\n{technical_investigation}"
    )


def generate_rca(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
    groq_api_key: str = "",
) -> Dict[str, Any]:
    """
    Generates a structured RCA using the fine-tuned SLM,
    then expands it to verbose enterprise prose using Groq.

    Args:
        problem_description:     What happened.
        business_impact:         Business consequences.
        technical_investigation: Timeline of events.
        groq_api_key:            Groq API key. If empty, skips expansion.

    Returns:
        Dict containing:
            five_why_analysis:       List of {question, answer} dicts.
            root_cause_summary:      Dict with statement + root_cause_category.
            parse_success:           Bool — False if SLM output unparseable.
            groq_available:          Bool — False if Groq was unreachable.
            hallucination_reverted:  Bool — True if Groq hallucinated and reverted.
            raw_output:              Raw SLM text for debugging.
    """
    prompt = build_rca_prompt(
        problem_description=problem_description,
        business_impact=business_impact,
        technical_investigation=technical_investigation,
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_rca_output(raw_output)

    if not success:
        logger.error("RCA generation produced unparseable output.")
        return {
            "five_why_analysis": [],
            "root_cause_summary": {},
            "parse_success": False,
            "groq_available": True,
            "hallucination_reverted": False,
            "raw_output": raw_output,
        }

    # ── Groq expansion ────────────────────────────────────
    groq_available = True
    hallucination_reverted = False

    if groq_api_key:
        incident_text = _build_incident_text(
            problem_description, business_impact, technical_investigation
        )
        parsed, groq_available, hallucination_reverted = expand_with_groq(
            groq_api_key=groq_api_key,
            slm_json=parsed,
            original_incident=incident_text,
        )
    else:
        logger.info("No Groq API key provided — skipping expansion.")

    return {
        "five_why_analysis": parsed.get("five_why_analysis", []),
        "root_cause_summary": parsed.get("root_cause_summary", {}),
        "parse_success": True,
        "groq_available": groq_available,
        "hallucination_reverted": hallucination_reverted,
        "raw_output": raw_output,
    }


def regenerate_rca(
    original_incident: Dict[str, str],
    previous_rca: Dict[str, Any],
    user_feedback: str,
    groq_api_key: str = "",
) -> Dict[str, Any]:
    """
    Regenerates RCA incorporating human reviewer feedback,
    then expands with Groq.

    Args:
        original_incident: Dict with problem_description, business_impact,
                           technical_investigation.
        previous_rca:      Previously generated RCA dict.
        user_feedback:     Human reviewer's feedback string.
        groq_api_key:      Groq API key.

    Returns:
        Same shape as generate_rca().
    """
    incident_text = _build_incident_text(
        original_incident.get("problem_description", ""),
        original_incident.get("business_impact", ""),
        original_incident.get("technical_investigation", ""),
    )

    prompt = build_rca_regeneration_prompt(
        original_incident=incident_text,
        previous_rca=json.dumps(previous_rca, indent=2),
        feedback=user_feedback,
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_rca_output(raw_output)

    if not success:
        logger.error("RCA regeneration produced unparseable output.")
        return {
            "five_why_analysis": [],
            "root_cause_summary": {},
            "parse_success": False,
            "groq_available": True,
            "hallucination_reverted": False,
            "raw_output": raw_output,
        }

    groq_available = True
    hallucination_reverted = False

    if groq_api_key:
        parsed, groq_available, hallucination_reverted = expand_with_groq(
            groq_api_key=groq_api_key,
            slm_json=parsed,
            original_incident=incident_text,
        )

    return {
        "five_why_analysis": parsed.get("five_why_analysis", []),
        "root_cause_summary": parsed.get("root_cause_summary", {}),
        "parse_success": True,
        "groq_available": groq_available,
        "hallucination_reverted": hallucination_reverted,
        "raw_output": raw_output,
    }