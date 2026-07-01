# ==========================================================
# capa_service.py
# Orchestrates the full CAPA generation pipeline:
#   1. Build prompt conditioned on approved RCA
#   2. Run SLM inference
#   3. Parse JSON output
#   4. Expand with Groq to verbose enterprise prose
#   5. Return structured dict + groq status flags
# ==========================================================

import json
import logging
from typing import Any, Dict, Tuple

from src.reasoning.inference import generate_output
from src.reasoning.prompts import (
    build_capa_prompt,
    build_capa_regeneration_prompt,
)
from src.reasoning.groq_expansion import expand_with_groq

logger = logging.getLogger(__name__)

REQUIRED_CAPA_KEYS = {"corrective_preventive_actions", "lessons_learned"}


def _parse_capa_output(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Parses and validates CAPA JSON output from the SLM.
    Checks for required keys, CA/PA presence, and non-empty lessons.

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
        logger.error(f"CAPA JSON parse failed: {e} | raw: {raw_text[:300]}")
        return {}, False

    missing = REQUIRED_CAPA_KEYS - set(data.keys())
    if missing:
        logger.warning(f"CAPA output missing required keys: {missing}")
        return data, False

    actions = data.get("corrective_preventive_actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        logger.warning("corrective_preventive_actions is empty or not a list")
        return data, False

    types = [a.get("action_type", "").upper() for a in actions]
    if not any("CA" in t or "CORRECTIVE" in t for t in types):
        logger.warning("CAPA output missing at least one CA action")
        return data, False
    if not any("PA" in t or "PREVENTIVE" in t for t in types):
        logger.warning("CAPA output missing at least one PA action")
        return data, False

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
    groq_api_key: str = "",
) -> Dict[str, Any]:
    """
    Generates structured CAPA conditioned on the approved RCA,
    then expands to verbose enterprise prose using Groq.

    Args:
        problem_description:     What happened.
        business_impact:         Business consequences.
        technical_investigation: Timeline of events.
        approved_rca:            Approved RCA dict from Task A.
        groq_api_key:            Groq API key. If empty, skips expansion.

    Returns:
        Dict with corrective_preventive_actions, lessons_learned,
        parse_success, groq_available, hallucination_reverted, raw_output.
    """
    prompt = build_capa_prompt(
        problem_description=problem_description,
        business_impact=business_impact,
        technical_investigation=technical_investigation,
        approved_rca=json.dumps(approved_rca, indent=2),
    )

    raw_output = generate_output(prompt)
    parsed, success = _parse_capa_output(raw_output)

    if not success:
        logger.error("CAPA generation produced unparseable output.")
        return {
            "corrective_preventive_actions": [],
            "lessons_learned": [],
            "parse_success": False,
            "groq_available": True,
            "hallucination_reverted": False,
            "raw_output": raw_output,
        }

    # ── Groq expansion ────────────────────────────────────
    groq_available = True
    hallucination_reverted = False

    if groq_api_key:
        # Build incident text as source-of-truth for hallucination check
        incident_text = (
            f"Problem Description:\n{problem_description}\n\n"
            f"Business Impact:\n{business_impact}\n\n"
            f"Technical Investigation:\n{technical_investigation}\n\n"
            f"Approved Root Cause:\n{json.dumps(approved_rca, indent=2)}"
        )
        parsed, groq_available, hallucination_reverted = expand_with_groq(
            groq_api_key=groq_api_key,
            slm_json=parsed,
            original_incident=incident_text,
        )
    else:
        logger.info("No Groq API key provided — skipping expansion.")

    return {
        "corrective_preventive_actions": parsed.get("corrective_preventive_actions", []),
        "lessons_learned": parsed.get("lessons_learned", []),
        "parse_success": True,
        "groq_available": groq_available,
        "hallucination_reverted": hallucination_reverted,
        "raw_output": raw_output,
    }


def regenerate_capa(
    original_incident: Dict[str, str],
    approved_rca: Dict[str, Any],
    previous_capa: Dict[str, Any],
    user_feedback: str,
    groq_api_key: str = "",
) -> Dict[str, Any]:
    """
    Regenerates CAPA incorporating human reviewer feedback,
    then expands with Groq.

    Args:
        original_incident: Dict with problem_description, business_impact,
                           technical_investigation.
        approved_rca:      Approved RCA — passed as context, not changed.
        previous_capa:     Previously generated CAPA dict.
        user_feedback:     Human reviewer's feedback string.
        groq_api_key:      Groq API key.

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
        logger.error("CAPA regeneration produced unparseable output.")
        return {
            "corrective_preventive_actions": [],
            "lessons_learned": [],
            "parse_success": False,
            "groq_available": True,
            "hallucination_reverted": False,
            "raw_output": raw_output,
        }

    groq_available = True
    hallucination_reverted = False

    if groq_api_key:
        full_incident_text = (
            f"{incident_text}\n\n"
            f"Approved Root Cause:\n{json.dumps(approved_rca, indent=2)}"
        )
        parsed, groq_available, hallucination_reverted = expand_with_groq(
            groq_api_key=groq_api_key,
            slm_json=parsed,
            original_incident=full_incident_text,
        )

    return {
        "corrective_preventive_actions": parsed.get("corrective_preventive_actions", []),
        "lessons_learned": parsed.get("lessons_learned", []),
        "parse_success": True,
        "groq_available": groq_available,
        "hallucination_reverted": hallucination_reverted,
        "raw_output": raw_output,
    }