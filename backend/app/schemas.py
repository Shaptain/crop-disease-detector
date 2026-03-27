"""
app/schemas.py
Pydantic models for API request and response validation.
"""

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response schema returned by POST /predict."""

    disease: str = Field(..., example="Tomato Late Blight")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.94)
    symptoms: str = Field(..., example="Dark water-soaked lesions on leaves")
    cure: str = Field(..., example="Apply copper-based fungicide; remove infected leaves")


class HealthResponse(BaseModel):
    status: str = Field(default="healthy")
    model_loaded: bool