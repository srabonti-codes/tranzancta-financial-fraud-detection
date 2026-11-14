from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import APP_NAME, APP_VERSION
from app.schemas import PredictionInput, PredictionResponse
from app.services.fraud_service import fraud_service

router = APIRouter(prefix="/api")


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check() -> dict:
    ready = fraud_service.is_ready()
    return {
        "status": "healthy" if ready else "degraded",
        "application": APP_NAME,
        "version": APP_VERSION,
        "model_loaded": ready,
        "prediction_ready": ready,
    }


@router.get("/model-info")
async def model_info() -> dict:
    return fraud_service.get_model_info()


@router.get("/metrics")
async def metrics() -> dict:
    return fraud_service.get_metrics()


@router.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictionInput) -> PredictionResponse:
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="The fraud scoring model is not ready.")
    return PredictionResponse(**fraud_service.predict(payload))
