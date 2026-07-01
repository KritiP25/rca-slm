# ==========================================================
# schemas.py
# Pydantic models for all API request and response bodies.
# RCAResponse and CAPAResponse return parsed dicts (not strings)
# so the frontend receives structured JSON it can work with directly.
# ==========================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Request schemas ───────────────────────────────────────

class RCARequest(BaseModel):
    """Input for /generate-rca endpoint."""
    problem_description: str
    business_impact: str
    technical_investigation: str


class CAPARequest(BaseModel):
    """Input for /generate-capa endpoint."""
    problem_description: str
    business_impact: str
    technical_investigation: str
    approved_rca: Dict[str, Any]   # Parsed RCA dict, not a string


class RegenerateRCARequest(BaseModel):
    """Input for /regenerate-rca endpoint."""
    original_incident: Dict[str, str]  # problem_description, business_impact, technical_investigation
    previous_rca: Dict[str, Any]       # Previously generated RCA dict
    user_feedback: str


class RegenerateCAPARequest(BaseModel):
    """Input for /regenerate-capa endpoint."""
    original_incident: Dict[str, str]
    approved_rca: Dict[str, Any]
    previous_capa: Dict[str, Any]
    user_feedback: str


class ReportRequest(BaseModel):
    """Input for /generate-report endpoint."""
    # User-provided metadata
    problem_number: str
    prepared_by: str
    problem_analyst: str
    impacted_location: str
    impacted_business_unit: str
    impacted_service_tower: str
    impacted_application: str
    # User-provided incident content
    problem_description: str
    business_impact: str
    technical_investigation: List[Dict[str, str]]  # [{date, time, activity}]
    related_tickets: Optional[List[Dict[str, str]]] = []  # [{ticket, reported, resolved, duration}]
    # AI-generated content
    five_why_analysis: List[Dict[str, str]]        # [{question, answer}]
    root_cause_summary: Dict[str, str]             # {statement, root_cause_category}
    corrective_preventive_actions: List[Dict[str, str]]  # [{action_type, action_description, action_owner}]
    lessons_learned: List[str]


# ── Response schemas ──────────────────────────────────────

class ValidationResult(BaseModel):
    """Validation outcome returned with every generation response."""
    passed: bool
    failure_type: Optional[str] = None   # None / "structure" / "content"
    issues: List[Dict[str, str]] = []    # [{type, issue}]
    warnings: List[Dict[str, str]] = []  # [{field, issue}] — non-blocking


class RCAResponse(BaseModel):
    """Response from /generate-rca and /regenerate-rca."""
    five_why_analysis: List[Dict[str, Any]]
    root_cause_summary: Dict[str, Any]
    validation: ValidationResult
    groq_available: bool = True   # False when Groq fallback was triggered


class CAPAResponse(BaseModel):
    """Response from /generate-capa and /regenerate-capa."""
    corrective_preventive_actions: List[Dict[str, Any]]
    lessons_learned: List[str]
    validation: ValidationResult
    groq_available: bool = True