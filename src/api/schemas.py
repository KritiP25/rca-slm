from pydantic import BaseModel


class RCARequest(BaseModel):

    problem_description: str

    business_impact: str

    technical_investigation: str


class RCAResponse(BaseModel):

    rca: str


class CAPARequest(BaseModel):

    problem_description: str

    business_impact: str

    technical_investigation: str

    approved_rca: str


class CAPAResponse(BaseModel):

    capa: str