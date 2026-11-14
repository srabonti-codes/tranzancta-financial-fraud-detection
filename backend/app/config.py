from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "Tranzacta")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
MODEL_PATH = Path(
    os.getenv("MODEL_PATH", BACKEND_DIR / "models" / "best_model.keras")
)
MODEL_METADATA_PATH = Path(
    os.getenv(
        "MODEL_METADATA_PATH",
        BACKEND_DIR / "models" / "best_model_metadata.json",
    )
)
PREPROCESSING_PATH = Path(
    os.getenv("PREPROCESSING_PATH", BACKEND_DIR / "artifacts" / "preprocessing.pkl")
)
