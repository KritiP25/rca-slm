# ==========================================================
# groq_expansion.py
# Expands the SLM's concise JSON output into verbose
# enterprise prose using Groq's Llama-3.3-70B model.
#
# Two prompt modes:
#   - Normal: first expansion attempt
#   - Repair: used when first attempt broke JSON structure
#
# Hallucination defence:
#   - Temperature set to 0.1 to minimise invention
#   - Strict system prompt forbids adding new facts
#   - Post-expansion diff check flags invented specifics
#   - If 3+ invented specifics found, reverts to SLM output
#
# Fallback: if Groq is unavailable, returns SLM output as-is
# and sets groq_available=False so frontend shows a banner.
# ==========================================================

import json
import logging
import re
from typing import Any, Dict, List, Tuple

from groq import Groq

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────

# Groq model — Llama 3.3 70B is free tier and handles
# enterprise prose expansion reliably
GROQ_MODEL = "llama-3.3-70b-versatile"

# Low temperature minimises hallucination during expansion
GROQ_TEMPERATURE = 0.1

# Number of invented specific claims that triggers revert to SLM output
HALLUCINATION_THRESHOLD = 3

# Regex patterns for detecting specific technical claims
# These are things Groq might invent that weren't in the original incident
SPECIFIC_CLAIM_PATTERNS = [
    r'\b[A-Z][a-z]+-\d+\b',          # Server names like Server-01, lb-prod-01
    r'\bv\d+\.\d+[\.\d]*\b',          # Version numbers like v2.3, v1.0.1
    r'\b\d{1,3}%\b',                  # Percentages like 99%, 15%
    r'\b(INC|PRB|CHG|REQ)\d+\b',      # Ticket IDs like INC0012345
    r'\b\d+\s*(hours?|minutes?|seconds?|days?)\b',  # Durations like 4 hours
]


# ── System prompts ────────────────────────────────────────

NORMAL_SYSTEM_PROMPT = """You are expanding an enterprise IT Root Cause Analysis report into verbose professional prose.

STRICT RULES — violating any of these is a failure:
1. You may ONLY elaborate on facts already present in the ORIGINAL INCIDENT or the RCA JSON provided
2. Do NOT add server names, tool names, ticket numbers, dates, percentages, or technical specifics unless they appear word-for-word in the source material
3. If you want to add context, use general language: 'the affected system' NOT 'Server-01'
4. Your job is to make existing content MORE DETAILED in language — not to ADD NEW FACTS
5. Each 5-Why answer should be expanded to 3-5 sentences of formal enterprise language
6. Root cause statement should be 2 detailed paragraphs
7. Each CAPA action_description should be a full detailed paragraph
8. Each lesson in lessons_learned should be 2-3 sentences
9. Return ONLY valid JSON with EXACTLY the same keys as the input JSON — no extra keys, no markdown, no backticks, no explanation"""

REPAIR_SYSTEM_PROMPT = """You are fixing a broken JSON expansion of an enterprise RCA report.

Your previous expansion attempt broke the JSON structure or introduced incorrect content.
You must fix this now.

STRICT RULES:
1. Return ONLY valid JSON — no markdown, no backticks, no explanation
2. Use EXACTLY the same keys as the ORIGINAL JSON provided — do not add or rename any keys
3. Do NOT add any technical specifics not present in the original incident text
4. Expand content to be more verbose and professional but stay factually grounded"""


def _extract_specific_claims(text: str) -> List[str]:
    """
    Extracts specific technical claims from text using regex patterns.
    Used to detect facts that Groq may have invented during expansion.
    """
    claims = []
    for pattern in SPECIFIC_CLAIM_PATTERNS:
        claims.extend(re.findall(pattern, text))
    return claims


def _check_hallucination(
    original_incident: str,
    slm_json: Dict[str, Any],
    groq_json: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Compares Groq output against the original incident and SLM output
    to detect invented specific technical claims.

    Returns:
        (hallucination_detected: bool, invented_claims: List[str])
    """
    # Build source text — everything that is allowed to appear in Groq output
    source_text = original_incident + " " + json.dumps(slm_json)

    # Extract claims from Groq output
    groq_text = json.dumps(groq_json)
    groq_claims = _extract_specific_claims(groq_text)

    # Find claims in Groq output that don't appear in source text
    invented = [
        claim for claim in groq_claims
        if claim not in source_text
    ]

    hallucination_detected = len(invented) >= HALLUCINATION_THRESHOLD

    if hallucination_detected:
        logger.warning(
            f"Hallucination detected — {len(invented)} invented claims: {invented}"
        )

    return hallucination_detected, invented


def _call_groq(
    client: Groq,
    system_prompt: str,
    user_message: str,
) -> Tuple[str, bool]:
    """
    Makes a single Groq API call.

    Returns:
        (response_text: str, success: bool)
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=GROQ_TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )
        return response.choices[0].message.content, True
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return "", False


def _parse_groq_response(text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Parses Groq's response as JSON.
    Strips markdown fences if present.

    Returns:
        (parsed_dict: dict, success: bool)
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        return json.loads(text), True
    except json.JSONDecodeError as e:
        logger.error(f"Groq response JSON parse failed: {e}")
        return {}, False


def expand_with_groq(
    groq_api_key: str,
    slm_json: Dict[str, Any],
    original_incident: str,
) -> Tuple[Dict[str, Any], bool, bool]:
    """
    Expands the SLM's JSON output to verbose enterprise prose using Groq.

    Attempt 1: Normal expansion prompt.
    Attempt 2 (if structure broken): Repair prompt showing the broken output.
    Fallback: If both fail or Groq is unavailable, return SLM output as-is.

    Args:
        groq_api_key:      Groq API key string.
        slm_json:          Parsed JSON dict from the SLM.
        original_incident: Full incident text (used for hallucination check).

    Returns:
        (result_json: dict, groq_available: bool, hallucination_reverted: bool)
        - result_json:           Final JSON to use (Groq or SLM fallback).
        - groq_available:        False if Groq was unreachable.
        - hallucination_reverted: True if Groq hallucinated and we reverted to SLM.
    """
    try:
        client = Groq(api_key=groq_api_key)
    except Exception as e:
        logger.error(f"Groq client init failed: {e}")
        return slm_json, False, False

    slm_json_str = json.dumps(slm_json, indent=2)

    user_message = (
        f"ORIGINAL INCIDENT (source of truth — only facts from here are allowed):\n"
        f"{original_incident}\n\n"
        f"JSON TO EXPAND:\n{slm_json_str}"
    )

    # ── Attempt 1: Normal expansion ───────────────────────
    raw_response, api_success = _call_groq(client, NORMAL_SYSTEM_PROMPT, user_message)

    if not api_success:
        # Groq is down or rate limited — use SLM output as fallback
        logger.warning("Groq unavailable — using raw SLM output as fallback.")
        return slm_json, False, False

    groq_json, parse_success = _parse_groq_response(raw_response)

    if not parse_success:
        # ── Attempt 2: Repair prompt ──────────────────────
        logger.warning("Groq response was invalid JSON — attempting repair.")
        repair_message = (
            f"Your previous response was invalid JSON. Here is what you returned:\n"
            f"{raw_response[:1000]}\n\n"
            f"Required JSON keys: {list(slm_json.keys())}\n\n"
            f"Original JSON to expand:\n{slm_json_str}"
        )
        raw_response, api_success = _call_groq(client, REPAIR_SYSTEM_PROMPT, repair_message)

        if not api_success:
            logger.warning("Groq repair attempt also failed — using SLM output.")
            return slm_json, False, False

        groq_json, parse_success = _parse_groq_response(raw_response)

        if not parse_success:
            # Both attempts failed — fall back to SLM output
            logger.warning("Groq repair produced invalid JSON — using SLM output.")
            return slm_json, True, False

    # ── Hallucination check ───────────────────────────────
    hallucinated, invented_claims = _check_hallucination(
        original_incident=original_incident,
        slm_json=slm_json,
        groq_json=groq_json,
    )

    if hallucinated:
        # Groq invented too many specifics — revert to SLM output
        logger.warning(
            f"Reverting to SLM output due to hallucination. "
            f"Invented claims: {invented_claims}"
        )
        return slm_json, True, True

    # ── Success ───────────────────────────────────────────
    logger.info("Groq expansion successful.")
    return groq_json, True, False