# ==========================================================
# routes/rca.py
# FastAPI route handlers for RCA generation and regeneration.
# Returns structured parsed JSON so the frontend receives
# typed data it can display directly.
# Groq API key is read from environment variable GROQ_API_KEY
# set in the Colab notebook at session start.
# ==========================================================

import os
import logging
from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    RCARequest,
    RCAResponse,
    RegenerateRCARequest,
    ValidationResult,
)
from src.reasoning.rca_service import generate_rca, regenerate_rca

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_validation_placeholder() -> ValidationResult:
    """
    Returns a passing validation result placeholder.
    Full validation (rule-based + semantic) will be added in a later step.
    """
    return ValidationResult(
        passed=True,
        failure_type=None,
        issues=[],
        warnings=[],
    )


@router.post("/generate-rca", response_model=RCAResponse)
def generate(request: RCARequest):
    """
    Generates a structured RCA from incident details.
    Pipeline: SLM inference → Groq expansion → return parsed JSON.
    Groq expansion is skipped if GROQ_API_KEY is not set.
    """
    try:
        result = generate_rca(
            problem_description=request.problem_description,
            business_impact=request.business_impact,
            technical_investigation=request.technical_investigation,
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
        )

        if not result["parse_success"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Model output could not be parsed as valid JSON",
                    "raw_output": result["raw_output"][:500],
                },
            )

        return RCAResponse(
            five_why_analysis=result["five_why_analysis"],
            root_cause_summary=result["root_cause_summary"],
            validation=_build_validation_placeholder(),
            groq_available=result["groq_available"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/generate-rca failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )


@router.post("/regenerate-rca", response_model=RCAResponse)
def regenerate(request: RegenerateRCARequest):
    """
    Regenerates RCA incorporating human reviewer feedback.
    Pipeline: SLM inference with feedback → Groq expansion → return JSON.
    """
    try:
        result = regenerate_rca(
            original_incident=request.original_incident,
            previous_rca=request.previous_rca,
            user_feedback=request.user_feedback,
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
        )

        if not result["parse_success"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Regenerated output could not be parsed as valid JSON",
                    "raw_output": result["raw_output"][:500],
                },
            )

        return RCAResponse(
            five_why_analysis=result["five_why_analysis"],
            root_cause_summary=result["root_cause_summary"],
            validation=_build_validation_placeholder(),
            groq_available=result["groq_available"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/regenerate-rca failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )