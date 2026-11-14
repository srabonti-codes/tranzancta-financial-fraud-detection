from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    transaction_type: Literal["TRANSFER", "CASH_OUT"]
    hour: int = Field(ge=0, le=23)
    amount: float = Field(ge=0)
    sender_balance_before: float = Field(ge=0)
    sender_balance_after: float = Field(ge=0)
    receiver_balance_before: float = Field(ge=0)
    receiver_balance_after: float = Field(ge=0)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prediction: Literal["high_risk", "low_risk"]
    fraud_probability: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    model_name: str
    recommendation: str
    status: Literal["success"] = "success"
