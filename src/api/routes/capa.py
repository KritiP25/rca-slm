# ==========================================================
# routes/capa.py
# FastAPI route handlers for CAPA generation and regeneration.
# CAPA is always conditioned on the approved RCA from Task A.
# ==========================================================

import logging
from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    CAPARequest,
    CAPAResponse,
    RegenerateCAPARequest,
    ValidationResult,
)
from src.reasoning.capa_service import generate_capa, regenerate_capa

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_validation_placeholder() -> ValidationResult:
    """
    Returns a passing validation result placeholder.
    Full validation will be added in a later step.
    """
    return ValidationResult(
        passed=True,
        failure_type=None,
        issues=[],
        warnings=[],
    )


@router.post("/generate-capa", response_model=CAPAResponse)
def generate(request: CAPARequest):
    """
    Generates structured CAPA conditioned on the approved RCA.
    The approved_rca field must be the parsed RCA dict from /generate-rca.
    """
    try:
        result = generate_capa(
            problem_description=request.problem_description,
            business_impact=request.business_impact,
            technical_investigation=request.technical_investigation,
            approved_rca=request.approved_rca,
        )

        if not result["parse_success"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Model output could not be parsed as valid JSON",
                    "raw_output": result["raw_output"][:500],
                },
            )

        return CAPAResponse(
            corrective_preventive_actions=result["corrective_preventive_actions"],
            lessons_learned=result["lessons_learned"],
            validation=_build_validation_placeholder(),
            groq_available=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/generate-capa failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )


@router.post("/regenerate-capa", response_model=CAPAResponse)
def regenerate(request: RegenerateCAPARequest):
    """
    Regenerates CAPA incorporating human reviewer feedback.
    The approved RCA is passed as context and remains unchanged.
    """
    try:
        result = regenerate_capa(
            original_incident=request.original_incident,
            approved_rca=request.approved_rca,
            previous_capa=request.previous_capa,
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

        return CAPAResponse(
            corrective_preventive_actions=result["corrective_preventive_actions"],
            lessons_learned=result["lessons_learned"],
            validation=_build_validation_placeholder(),
            groq_available=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/regenerate-capa failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )