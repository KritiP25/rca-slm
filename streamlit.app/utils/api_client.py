# ==========================================================
# api_client.py
# Handles all HTTP communication between the Streamlit
# frontend and the FastAPI backend running in Colab.
#
# All functions return a dict with either the response data
# or an error key so callers never need to handle exceptions.
# Timeouts are generous because model inference takes 15-30s
# and Groq expansion adds another 3-5s on top.
# ==========================================================

import requests
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Import backend URL from config — update config.py each session
from utils.config import BACKEND_URL

# Request timeout in seconds — model inference + Groq expansion
TIMEOUT = 180


def _post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Makes a POST request to the backend.
    Returns response dict on success, or {"error": message} on failure.
    Never raises — all exceptions are caught and returned as error dicts.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            # Try to extract structured error from FastAPI response
            try:
                detail = response.json().get("detail", {})
                error_msg = detail.get("error", str(detail)) if isinstance(detail, dict) else str(detail)
            except Exception:
                error_msg = response.text[:300]
            logger.error(f"POST {endpoint} failed [{response.status_code}]: {error_msg}")
            return {"error": error_msg}
    except requests.exceptions.Timeout:
        msg = f"Request timed out after {TIMEOUT}s — model may need more time."
        logger.error(msg)
        return {"error": msg}
    except requests.exceptions.ConnectionError:
        msg = "Cannot reach backend. Check that Colab is running and the Cloudflare tunnel is active."
        logger.error(msg)
        return {"error": msg}
    except Exception as e:
        logger.error(f"POST {endpoint} unexpected error: {e}")
        return {"error": str(e)}


def _get(endpoint: str) -> Dict[str, Any]:
    """
    Makes a GET request to the backend.
    Returns response dict on success, or {"error": message} on failure.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach backend. Check Colab and Cloudflare tunnel."}
    except Exception as e:
        return {"error": str(e)}


def health_check() -> bool:
    """
    Checks if the backend is reachable and running.
    Returns True if healthy, False otherwise.
    """
    result = _get("/")
    return "error" not in result


def generate_rca(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
) -> Dict[str, Any]:
    """
    Calls POST /generate-rca.
    Pipeline: SLM inference → Groq expansion → validation.

    Returns dict with:
        five_why_analysis, root_cause_summary, validation, groq_available
    Or {"error": message} on failure.
    """
    return _post("/generate-rca", {
        "problem_description":    problem_description,
        "business_impact":        business_impact,
        "technical_investigation": technical_investigation,
    })


def regenerate_rca(
    original_incident: Dict[str, str],
    previous_rca: Dict[str, Any],
    user_feedback: str,
) -> Dict[str, Any]:
    """
    Calls POST /regenerate-rca with human feedback.
    Used when user clicks Regenerate RCA after providing feedback.

    Returns same shape as generate_rca().
    """
    return _post("/regenerate-rca", {
        "original_incident": original_incident,
        "previous_rca":      previous_rca,
        "user_feedback":     user_feedback,
    })


def generate_capa(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
    approved_rca: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calls POST /generate-capa.
    CAPA is conditioned on the approved RCA — Task B pipeline.

    Returns dict with:
        corrective_preventive_actions, lessons_learned, validation, groq_available
    Or {"error": message} on failure.
    """
    return _post("/generate-capa", {
        "problem_description":    problem_description,
        "business_impact":        business_impact,
        "technical_investigation": technical_investigation,
        "approved_rca":           approved_rca,
    })


def regenerate_capa(
    original_incident: Dict[str, str],
    approved_rca: Dict[str, Any],
    previous_capa: Dict[str, Any],
    user_feedback: str,
) -> Dict[str, Any]:
    """
    Calls POST /regenerate-capa with human feedback.
    The approved RCA stays unchanged — only CAPA is regenerated.

    Returns same shape as generate_capa().
    """
    return _post("/regenerate-capa", {
        "original_incident": original_incident,
        "approved_rca":      approved_rca,
        "previous_capa":     previous_capa,
        "user_feedback":     user_feedback,
    })


def generate_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls POST /generate-report.
    Sends all approved content + metadata to generate DOCX and PDF.

    Returns dict with:
        status, docx_available, pdf_available, docx_url, pdf_url
    Or {"error": message} on failure.
    """
    return _post("/generate-report", report_data)


def download_file(endpoint: str) -> bytes | None:
    """
    Downloads a binary file (DOCX or PDF) from the backend.
    Returns raw bytes on success, None on failure.

    Args:
        endpoint: "/download-docx" or "/download-pdf"
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return response.content
        logger.error(f"Download {endpoint} failed: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Download {endpoint} error: {e}")
        return None