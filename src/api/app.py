# ==========================================================
# app.py
# FastAPI application entry point.
# Registers all route handlers and defines the health check.
# ==========================================================

from fastapi import FastAPI

from src.api.routes.rca    import router as rca_router
from src.api.routes.capa   import router as capa_router
from src.api.routes.report import router as report_router

app = FastAPI(
    title="RCA-SLM API",
    version="1.0.0",
)

app.include_router(rca_router)
app.include_router(capa_router)
app.include_router(report_router)


@app.get("/")
def home():
    """Health check endpoint — confirms the server is running."""
    return {"message": "RCA-SLM Backend Running"}