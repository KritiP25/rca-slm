from fastapi import APIRouter

from src.api.schemas import (
    RCARequest,
    RCAResponse,
)

from src.reasoning.rca_service import generate_rca

router = APIRouter()


@router.post(
    "/generate-rca",
    response_model=RCAResponse,
)
def generate(request: RCARequest):

    result = generate_rca(

        request.problem_description,

        request.business_impact,

        request.technical_investigation,

    )

    return RCAResponse(
        rca=result
    )