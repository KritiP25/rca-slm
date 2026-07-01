# ==========================================================
# rca_service.py
# Orchestrates the full RCA generation pipeline:
#   1. Build prompt (task-prefixed, matching training format)
#   2. Run SLM inference
#   3. Parse JSON output
#   4. Strip issue_summary if model still produces it
#   5. Return structured dict + validation placeholder
#
# Groq expansion and validation will be layered on top in
# subsequent steps. This file handles SLM inference only.
# ==========================================================

import json
import logging
from typing import Any, Dict, Tuple

from src.reasoning.inference import generate_output
from src.reasoning.prompts import (
    build_rca_prompt,
    build_rca_regeneration_prompt,
)

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────
# Required top-level keys in a valid RCA JSON output.
# issue_summary is intentionally absent — removed from schema.
REQUIRED_RCA_KEYS = {"five_why_analysis", "root_cause_summary"}


def _parse_rca_output(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Attempts to parse the model's raw text output as JSON.

    Strips issue_summary if the model still produces it
    (model was trained on old format — prompt fix reduces this
    but does not guarantee elimination immediately).

    Returns:
        (parsed_dict, success_bool)
        On failure returns (empty dict, False).
    """
    # Strip any accidental markdown code fences the model may add
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"RCA JSON parse failed: {e} | raw output: {raw_text[:300]}")
        return {}, False

    # Remove issue_summary if model still outputs it
    data.pop("issue_summary", None)

    # Validate required keys are present
    missing = REQUIRED_RCA_KEYS - set(data.keys())
    if missing:
        logger.warning(f"RCA output missing required keys: {missing}")
        return data, False

    # Validate five_why_analysis is a non-empty list
    five_why = data.get("five_why_analysis", [])
    if not isinstance(five_why, list) or len(five_why) == 0:
        logger.warning("five_why_analysis is empty or not a list")
        return data, False

    # Validate root_cause_summary has required subkeys
    rcs = data.get("root_cause_summary", {})
    if not rcs.get("statement") or not rcs.get("root_cause_category"):
        logger.warning("root_cause_summary missing statement or root_cause_category")
        return data, False

    return data, True


def generate_rca(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
) -> Dict[str, Any]:
    """
    Generates a structured RCA using the fine-tuned SLM.

    Args:
        problem_description:     What happened.
        business_impact:         Business consequences.
        technical_investigation: Timeline of events.

    Returns:
        Dict containing:
            five_why_analysis:   List of {question, answer} dicts.
            root_cause_summary:  Dict with statement + root_cause_category.
            parse_success:       Bool — False means raw output could not be parsed.
            raw_output:          Raw model text (for debugging + fallback).
    """
    # Build the prompt using the task-prefixed format matching training data
    prompt = build_rca_prompt(
        problem_description=problem_description,
        business_impact=business_impact,
        technical_investigation=technical_investigation,
    )

    # Run SLM inference
    raw_output = generate_output(prompt)

    # Parse and validate the JSON output
    parsed, success = _parse_rca_output(raw_output)

    if not success:
        logger.error("RCA generation produced unparseable or incomplete output.")

    return {
        "five_why_analysis": parsed.get("five_why_analysis", []),
        "root_cause_summary": parsed.get("root_cause_summary", {}),
        "parse_success": success,
        "raw_output": raw_output,  # Kept for debugging and fallback handling
    }


def regenerate_rca(
    original_incident: Dict[str, str],
    previous_rca: Dict[str, Any],
    user_feedback: str,
) -> Dict[str, Any]:
    """
    Regenerates RCA incorporating human reviewer feedback.

    Args:
        original_incident: Dict with problem_description, business_impact,
                           technical_investigation.
        previous_rca:      Previously generated RCA dict (will be shown to model).
        user_feedback:     Human reviewer's feedback string.

    Returns:
        Same shape as generate_rca().
    """
    # Combine incident fields into a single string for the prompt
    incident_text = (
        f"Problem Description:\n{original_incident.get('problem_description', '')}\n\n"
        f"Business Impact:\n{original_incident.get('business_impact', '')}\n\n"
        f"Technical Investigation:\n{original_incident.get('technical_investigation', '')}"
    )

    # Serialize previous RCA to string for inclusion in prompt
    previous_rca_text = json.dumps(previous_rca, indent=2)

    prompt = build_rca_regeneration_prompt(
        original_incident=incident_text,
        previous_rca=previous_rca_text,
        feedback=user_feedback,
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_rca_output(raw_output)

    if not success:
        logger.error("RCA regeneration produced unparseable or incomplete output.")

    return {
        "five_why_analysis": parsed.get("five_why_analysis", []),
        "root_cause_summary": parsed.get("root_cause_summary", {}),
        "parse_success": success,
        "raw_output": raw_output,
    }