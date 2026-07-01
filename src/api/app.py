# ==========================================================
# app.py
# FastAPI application entry point.
# Registers all route handlers and defines the health check.
# New: capa_router added for /generate-capa and /regenerate-capa
# ==========================================================

from fastapi import FastAPI

from src.api.routes.rca import router as rca_router
from src.api.routes.capa import router as capa_router

app = FastAPI(
    title="RCA-SLM API",
    version="1.0.0",
)

# Register RCA routes — /generate-rca and /regenerate-rca
app.include_router(rca_router)

# Register CAPA routes — /generate-capa and /regenerate-capa
app.include_router(capa_router)


@app.get("/")
def home():
    """Health check endpoint — confirms the server is running."""
    return {"message": "RCA-SLM Backend Running"}