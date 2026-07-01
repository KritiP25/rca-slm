# ==========================================================
# capa_service.py
# Orchestrates the full CAPA generation pipeline:
#   1. Build prompt (task-prefixed, matching training format)
#   2. Run SLM inference conditioned on approved RCA
#   3. Parse JSON output
#   4. Return structured dict
#
# Task B was trained to receive the approved RCA as input
# so CAPA is conditioned on the root cause — not generated
# independently. This is the key architectural difference
# from the old single-task approach.
# ==========================================================

import json
import logging
from typing import Any, Dict, Tuple

from src.reasoning.inference import generate_output
from src.reasoning.prompts import (
    build_capa_prompt,
    build_capa_regeneration_prompt,
)

logger = logging.getLogger(__name__)

# Required top-level keys in a valid CAPA JSON output
REQUIRED_CAPA_KEYS = {"corrective_preventive_actions", "lessons_learned"}


def _parse_capa_output(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Attempts to parse the model's raw text output as JSON.

    Validates that both required keys are present and that
    at least one CA and one PA action exist in the list.

    Returns:
        (parsed_dict, success_bool)
        On failure returns (empty dict, False).
    """
    # Strip accidental markdown code fences
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"CAPA JSON parse failed: {e} | raw: {raw_text[:300]}")
        return {}, False

    # Validate required keys
    missing = REQUIRED_CAPA_KEYS - set(data.keys())
    if missing:
        logger.warning(f"CAPA output missing required keys: {missing}")
        return data, False

    # Validate actions list is non-empty
    actions = data.get("corrective_preventive_actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        logger.warning("corrective_preventive_actions is empty or not a list")
        return data, False

    # Validate at least one CA and one PA exist
    types = [a.get("action_type", "").upper() for a in actions]
    has_ca = any("CA" in t or "CORRECTIVE" in t for t in types)
    has_pa = any("PA" in t or "PREVENTIVE" in t for t in types)

    if not has_ca:
        logger.warning("CAPA output missing at least one CA action")
        return data, False
    if not has_pa:
        logger.warning("CAPA output missing at least one PA action")
        return data, False

    # Validate lessons_learned is non-empty
    lessons = data.get("lessons_learned", [])
    if not isinstance(lessons, list) or len(lessons) == 0:
        logger.warning("lessons_learned is empty or not a list")
        return data, False

    return data, True


def generate_capa(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
    approved_rca: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates structured CAPA using the fine-tuned SLM.
    CAPA is conditioned on the approved RCA — this is Task B.

    Args:
        problem_description:     What happened.
        business_impact:         Business consequences.
        technical_investigation: Timeline of events.
        approved_rca:            Approved RCA dict from Task A.

    Returns:
        Dict containing:
            corrective_preventive_actions: List of {action_type, action_description, action_owner}.
            lessons_learned:               List of strings.
            parse_success:                 Bool — False if output could not be parsed.
            raw_output:                    Raw model text for debugging.
    """
    # Serialize the approved RCA dict to a JSON string for inclusion in prompt
    approved_rca_text = json.dumps(approved_rca, indent=2)

    prompt = build_capa_prompt(
        problem_description=problem_description,
        business_impact=business_impact,
        technical_investigation=technical_investigation,
        approved_rca=approved_rca_text,
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_capa_output(raw_output)

    if not success:
        logger.error("CAPA generation produced unparseable or incomplete output.")

    return {
        "corrective_preventive_actions": parsed.get("corrective_preventive_actions", []),
        "lessons_learned": parsed.get("lessons_learned", []),
        "parse_success": success,
        "raw_output": raw_output,
    }


def regenerate_capa(
    original_incident: Dict[str, str],
    approved_rca: Dict[str, Any],
    previous_capa: Dict[str, Any],
    user_feedback: str,
) -> Dict[str, Any]:
    """
    Regenerates CAPA incorporating human reviewer feedback.
    The approved RCA stays unchanged — only CAPA is regenerated.

    Args:
        original_incident: Dict with problem_description, business_impact,
                           technical_investigation.
        approved_rca:      Approved RCA dict — passed as context, not changed.
        previous_capa:     Previously generated CAPA dict.
        user_feedback:     Human reviewer's feedback string.

    Returns:
        Same shape as generate_capa().
    """
    incident_text = (
        f"Problem Description:\n{original_incident.get('problem_description', '')}\n\n"
        f"Business Impact:\n{original_incident.get('business_impact', '')}\n\n"
        f"Technical Investigation:\n{original_incident.get('technical_investigation', '')}"
    )

    prompt = build_capa_regeneration_prompt(
        original_incident=incident_text,
        approved_rca=json.dumps(approved_rca, indent=2),
        previous_capa=json.dumps(previous_capa, indent=2),
        feedback=user_feedback,
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_capa_output(raw_output)

    if not success:
        logger.error("CAPA regeneration produced unparseable or incomplete output.")

    return {
        "corrective_preventive_actions": parsed.get("corrective_preventive_actions", []),
        "lessons_learned": parsed.get("lessons_learned", []),
        "parse_success": success,
        "raw_output": raw_output,
    }