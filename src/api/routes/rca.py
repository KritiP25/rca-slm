# ==========================================================
# routes/rca.py
# FastAPI route handlers for RCA generation and regeneration.
# Returns structured parsed JSON (not raw strings) so the
# frontend receives typed data it can display directly.
# ==========================================================

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
    For now this allows the endpoint to return the correct response shape.
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
    Calls the SLM inference pipeline and returns parsed JSON.
    """
    try:
        result = generate_rca(
            problem_description=request.problem_description,
            business_impact=request.business_impact,
            technical_investigation=request.technical_investigation,
        )

        # If parsing failed, return a 422 with the raw output for debugging
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
            groq_available=True,
        )

    except HTTPException:
        raise   # Re-raise HTTP exceptions as-is
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
    """
    try:
        result = regenerate_rca(
            original_incident=request.original_incident,
            previous_rca=request.previous_rca,
            user_feedback=request.user_feedback,
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
            groq_available=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/regenerate-rca failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )