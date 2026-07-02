# ==========================================================
# routes/report.py
# FastAPI route handler for report generation.
# Accepts all approved content + user metadata, generates
# a populated DOCX from the template and converts to PDF,
# then returns both files as downloadable responses.
# ==========================================================

import logging
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.api.schemas import ReportRequest
from src.api.report_generator import generate_report

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-report")
def generate(request: ReportRequest):
    """
    Generates the final RCA report as DOCX and PDF.
    Returns JSON with download URLs for both files.
    The files are served via /download-docx and /download-pdf.
    """
    try:
        result = generate_report(request.model_dump())

        return {
            "status": "success",
            "docx_available": bool(result["docx_path"]),
            "pdf_available":  bool(result["pdf_path"]),
            "docx_url": "/download-docx",
            "pdf_url":  "/download-pdf",
        }

    except FileNotFoundError as e:
        logger.error(f"Template missing: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"/generate-report failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "fallback_available": False},
        )


@router.get("/download-docx")
def download_docx():
    """Serves the generated DOCX file for download."""
    path = "/content/rca-slm/outputs/rca_report.docx"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="DOCX not found. Generate report first.")
    return FileResponse(
        path=path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="RCA_Report.docx",
    )


@router.get("/download-pdf")
def download_pdf():
    """Serves the generated PDF file for download."""
    path = "/content/rca-slm/outputs/rca_report.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found. Generate report first.")
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="RCA_Report.pdf",
    )