from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import ALLOWED_ORIGINS, APP_ENV, APP_NAME, APP_VERSION
from app.services.fraud_service import fraud_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Tranzacta transaction risk scoring API.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/")
async def root() -> dict:
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "documentation": "/api/docs",
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    ready = fraud_service.is_ready()
    return {
        "status": "healthy" if ready else "degraded",
        "application": APP_NAME,
        "version": APP_VERSION,
        "model_loaded": ready,
        "prediction_ready": ready,
    }
