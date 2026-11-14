from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services.fraud_service import FraudDetectionService, fraud_service

client = TestClient(app)
VALID_PAYLOAD = {
    "transaction_type": "TRANSFER",
    "hour": 14,
    "amount": 1250.0,
    "sender_balance_before": 5000.0,
    "sender_balance_after": 3750.0,
    "receiver_balance_before": 10000.0,
    "receiver_balance_after": 11250.0,
}


def test_root_and_health_endpoints() -> None:
    assert app.title == "Tranzacta"
    assert client.get("/").json()["application"] == "Tranzacta"
    health = client.get("/api/health").json()
    assert health["application"] == "Tranzacta"
    ready = fraud_service.is_ready()
    assert health["status"] == ("healthy" if ready else "degraded")
    assert health["prediction_ready"] is ready
    assert health["model_loaded"] is ready
    head = client.head("/api/health")
    assert head.status_code == 200
    assert head.content == b""


def test_model_information_and_metrics_endpoints() -> None:
    model_info = client.get("/api/model-info")
    metrics = client.get("/api/metrics")
    assert model_info.status_code == 200
    assert model_info.json()["application"] == "Tranzacta"
    assert model_info.json()["model_loaded"] is fraud_service.is_ready()
    assert metrics.status_code == 200
    assert metrics.json()["application"] == "Tranzacta"
    assert metrics.json()["model_loaded"] is fraud_service.is_ready()


def test_service_is_unavailable_without_local_artifacts(tmp_path) -> None:
    service = FraudDetectionService(
        model_path=tmp_path / "best_model.keras",
        metadata_path=tmp_path / "metadata.json",
        preprocessing_path=tmp_path / "preprocessing.pkl",
    )

    assert service.is_ready() is False
    assert service.model_name == "Unavailable"
    assert isinstance(service.load_error, FileNotFoundError)


def test_invalid_prediction_payload_is_rejected() -> None:
    invalid_payload = {**VALID_PAYLOAD, "hour": 24}
    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_prediction_response_from_ready_service(monkeypatch) -> None:
    expected = {
        "prediction": "low_risk",
        "fraud_probability": 0.12,
        "threshold": 0.49,
        "model_name": "MLP",
        "recommendation": "Low model-estimated risk; continue standard transaction controls.",
        "status": "success",
    }

    class ReadyService:
        @staticmethod
        def is_ready() -> bool:
            return True

        @staticmethod
        def predict(_payload):
            return expected

    monkeypatch.setattr(routes, "fraud_service", ReadyService())
    response = client.post("/api/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == expected


def test_unready_service_rejects_prediction(monkeypatch) -> None:
    class UnreadyService:
        @staticmethod
        def is_ready() -> bool:
            return False

    monkeypatch.setattr(routes, "fraud_service", UnreadyService())
    response = client.post("/api/predict", json=VALID_PAYLOAD)
    assert response.status_code == 503


def test_feature_engineering_preserves_training_feature_order() -> None:
    service = FraudDetectionService.__new__(FraudDetectionService)
    service.model = SimpleNamespace(
        predict=lambda _features, verbose=0: [[0.8]]
    )
    service.model_metadata = {
        "model_name": "MLP",
        "decision_threshold": {"threshold": 0.49},
    }
    service.model_name = "MLP"
    captured = {}

    def transform(frame):
        captured["columns"] = list(frame.columns)
        captured["values"] = frame.iloc[0].to_dict()
        return frame.to_numpy()

    service.preprocessing = {
        "feature_cols": [
            "log_amount",
            "error_orig",
            "error_dest",
            "hour",
            "is_night",
            "is_high_amount",
            "type_encoded",
            "oldbalanceOrg",
            "newbalanceOrig",
            "oldbalanceDest",
            "newbalanceDest",
        ],
        "metadata": {
            "type_mapping": {"TRANSFER": 0, "CASH_OUT": 1},
            "high_amount_threshold": 1_000_000,
        },
        "scaler": SimpleNamespace(transform=transform),
    }

    result = service.predict(
        type("Payload", (), VALID_PAYLOAD)()
    )
    assert result["prediction"] == "high_risk"
    assert result["fraud_probability"] == 0.8
    assert captured["columns"] == service.preprocessing["feature_cols"]
    assert captured["values"]["hour"] == 14
    assert captured["values"]["type_encoded"] == 0
