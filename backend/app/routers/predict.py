"""
app/routers/predict.py

Defines the POST /predict endpoint.

Flow:
  1. Receive uploaded image via multipart/form-data.
  2. Preprocess image (resize, normalise) via image_utils.
  3. Run model inference via model_service.
  4. Look up disease metadata via disease_service.
  5. Return structured JSON response.
"""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import PredictionResponse
from app.services import disease_service, model_service
from app.utils.image_utils import read_and_preprocess

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict crop disease from a leaf image",
    responses={
        200: {"description": "Prediction returned successfully"},
        400: {"description": "Invalid image file"},
        413: {"description": "File too large (max 10 MB)"},
        503: {"description": "Model not loaded"},
    },
)
async def predict_disease(
    file: UploadFile = File(..., description="Leaf image (JPEG or PNG, max 10 MB)"),
) -> PredictionResponse:
    """
    Upload a plant leaf image and receive:
    - **disease** — predicted disease name
    - **confidence** — model confidence (0.0 – 1.0)
    - **symptoms** — description of disease symptoms
    - **cure** — recommended treatment steps

    A confidence below 0.60 triggers a 'low confidence' response
    asking the user to retake the photo.
    """

    # --- Guard: model must be ready before accepting requests ---
    if not model_service.is_model_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. The service is unavailable. "
                   "Please contact the administrator.",
        )

    # --- Step 1: Read and preprocess the uploaded image ---
    # Raises HTTP 400 / 413 on invalid input (handled inside image_utils).
    try:
        img_array = await read_and_preprocess(file)
    except HTTPException:
        raise  # re-raise validation errors as-is
    except Exception as exc:
        logger.exception("Unexpected error during image preprocessing.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading the image.",
        ) from exc

    # --- Step 2: Run model inference ---
    try:
        class_label, confidence = model_service.predict(img_array)
    except RuntimeError as exc:
        logger.error("Model inference failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during model inference.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during prediction.",
        ) from exc

    # --- Step 3: Low-confidence guard ---
    if confidence < model_service.CONFIDENCE_THRESHOLD:
        logger.info(
            "Low confidence prediction (%.4f) for label '%s'. Returning advisory.",
            confidence,
            class_label,
        )
        return PredictionResponse(
            disease="Uncertain",
            confidence=round(confidence, 4),
            symptoms="The model could not identify the disease with sufficient confidence.",
            cure="Please retake the photo in good lighting, ensuring the affected leaf "
                 "fills the frame. If the problem persists, consult an agronomist.",
        )

    # --- Step 4: Fetch disease metadata from JSON database ---
    disease_info = disease_service.get_disease_info(class_label)

    # --- Step 5: Return structured response ---
    return PredictionResponse(
        disease=disease_info["display_name"],
        confidence=round(confidence, 4),
        symptoms=disease_info["symptoms"],
        cure=disease_info["cure"],
    )