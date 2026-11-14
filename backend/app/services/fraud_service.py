from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config import APP_NAME, MODEL_METADATA_PATH, MODEL_PATH, PREPROCESSING_PATH
from app.schemas import PredictionInput

logger = logging.getLogger(__name__)


class FraudDetectionService:
    def __init__(
        self,
        model_path: str | Path = MODEL_PATH,
        metadata_path: str | Path = MODEL_METADATA_PATH,
        preprocessing_path: str | Path = PREPROCESSING_PATH,
    ) -> None:
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.preprocessing_path = Path(preprocessing_path)
        self.model: Any = None
        self.model_metadata: dict[str, Any] = {}
        self.preprocessing: dict[str, Any] = {}
        self.model_name = "Unavailable"
        self.load_error: Exception | None = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        try:
            with self.metadata_path.open(encoding="utf-8") as file:
                self.model_metadata = json.load(file)
            with self.preprocessing_path.open("rb") as file:
                self.preprocessing = pickle.load(file)

            model_name = self.model_metadata["model_name"]
            if self.model_metadata.get("model_family") != "keras":
                raise ValueError("The configured production model is not a Keras model.")
            if not self.model_path.is_file():
                raise FileNotFoundError(f"Model artifact not found: {self.model_path}")

            from tensorflow.keras.models import load_model

            self.model = load_model(self.model_path)
            self.model_name = str(model_name)
        except FileNotFoundError as exc:
            self.model = None
            self.model_name = "Unavailable"
            self.load_error = exc
            logger.warning("Tranzacta model artifacts are unavailable: %s", exc)
        except Exception as exc:
            self.model = None
            self.model_name = "Unavailable"
            self.load_error = exc
            logger.exception("Could not load Tranzacta model artifacts.")

    def is_ready(self) -> bool:
        return (
            self.model is not None
            and bool(self.preprocessing.get("feature_cols"))
            and self.preprocessing.get("scaler") is not None
        )

    def _build_model_input(self, payload: PredictionInput) -> np.ndarray:
        if not self.is_ready():
            raise RuntimeError("The fraud scoring model is not ready.")

        preprocessing_metadata = self.preprocessing["metadata"]
        type_mapping = preprocessing_metadata["type_mapping"]
        transaction_type = payload.transaction_type
        if transaction_type not in type_mapping:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        hour = payload.hour
        amount = payload.amount
        feature_values = {
            "log_amount": np.log1p(amount),
            "error_orig": (
                payload.sender_balance_before - amount - payload.sender_balance_after
            ),
            "error_dest": (
                payload.receiver_balance_before + amount - payload.receiver_balance_after
            ),
            "hour": hour,
            "is_night": int(hour >= 22 or hour <= 5),
            "is_high_amount": int(
                amount > float(preprocessing_metadata["high_amount_threshold"])
            ),
            "type_encoded": int(type_mapping[transaction_type]),
            "oldbalanceOrg": payload.sender_balance_before,
            "newbalanceOrig": payload.sender_balance_after,
            "oldbalanceDest": payload.receiver_balance_before,
            "newbalanceDest": payload.receiver_balance_after,
        }
        feature_columns = list(self.preprocessing["feature_cols"])
        frame = pd.DataFrame(
            [{column: feature_values.get(column, 0) for column in feature_columns}],
            columns=feature_columns,
        )
        return self.preprocessing["scaler"].transform(frame).astype("float32")

    def predict(self, payload: PredictionInput) -> dict[str, Any]:
        model_input = self._build_model_input(payload)
        raw_probability = np.asarray(
            self.model.predict(model_input, verbose=0)
        ).ravel()[0]
        probability = float(raw_probability)
        if not np.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("The model returned an invalid fraud probability.")

        threshold = float(self.model_metadata["decision_threshold"]["threshold"])
        high_risk = probability >= threshold
        return {
            "prediction": "high_risk" if high_risk else "low_risk",
            "fraud_probability": probability,
            "threshold": threshold,
            "model_name": self.model_name,
            "recommendation": (
                "Hold for manual review before processing."
                if high_risk
                else "Low model-estimated risk; continue standard transaction controls."
            ),
            "status": "success",
        }

    def get_model_info(self) -> dict[str, Any]:
        return {
            "application": APP_NAME,
            "model_loaded": self.is_ready(),
            "model_name": self.model_name,
            "model_family": self.model_metadata.get("model_family"),
            "supported_transaction_types": ["TRANSFER", "CASH_OUT"],
            "feature_columns": self.preprocessing.get("feature_cols", []),
            "decision_threshold": self.model_metadata.get("decision_threshold", {}).get(
                "threshold"
            ),
            "dataset": "PaySim synthetic mobile money transactions",
        }

    def get_metrics(self) -> dict[str, Any]:
        return {
            "application": APP_NAME,
            "model_loaded": self.is_ready(),
            "model_name": self.model_name,
            "metrics": self.model_metadata.get("selection_metrics", {}),
            "decision_threshold": self.model_metadata.get("decision_threshold", {}),
            "dataset": "PaySim synthetic mobile money transactions",
        }


fraud_service = FraudDetectionService()
