"""
app/services/model_service.py

Loads the trained MobileNetV2 model ONCE at module import time
and exposes a predict() function used by the prediction router.

The class index → label mapping mirrors the folder order used
during training (PlantVillage dataset, 38 classes, sorted alphabetically).
Adjust CLASS_LABELS to match your own training order.
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Class label mapping — must match the order used during model training.
# PlantVillage 38-class sorted list (abbreviated here; extend as needed).
# ---------------------------------------------------------------------------
CLASS_LABELS = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

# Minimum softmax probability to trust a prediction.
# Below this threshold the response flags low confidence.
CONFIDENCE_THRESHOLD = 0.60

# Path to the saved Keras model weights
_MODEL_PATH = Path(__file__).resolve().parents[2] / "model" / "plant_disease_model.h5"

# ---------------------------------------------------------------------------
# Model loading — happens once when the module is first imported.
# ---------------------------------------------------------------------------
_model = None

try:
    # Import TensorFlow lazily so the app can start (with degraded behaviour)
    # even if TF is not installed, letting other endpoints remain reachable.
    import tensorflow as tf

    if _MODEL_PATH.exists():
        logger.info("Loading model from %s ...", _MODEL_PATH)
        _model = tf.keras.models.load_model(str(_MODEL_PATH))
        logger.info("Model loaded successfully.")
    else:
        logger.warning(
            "Model file not found at %s. "
            "Place your trained .h5 file there before sending predictions.",
            _MODEL_PATH,
        )
except ImportError:
    logger.error("TensorFlow is not installed. Install it with: pip install tensorflow")


def is_model_loaded() -> bool:
    """Return True if the Keras model is in memory and ready."""
    return _model is not None


def predict(img_array: np.ndarray) -> Tuple[str, float]:
    """
    Run inference on a preprocessed image array.

    Args:
        img_array: numpy array of shape (1, 224, 224, 3), values in [0, 1].

    Returns:
        Tuple of (class_label: str, confidence: float).

    Raises:
        RuntimeError: if the model has not been loaded.
    """
    if _model is None:
        raise RuntimeError(
            "Model is not loaded. Check that plant_disease_model.h5 "
            "exists in the model/ directory."
        )

    # Run forward pass — output shape: (1, num_classes)
    predictions = _model.predict(img_array, verbose=0)

    # Highest softmax probability and its index
    confidence: float = float(np.max(predictions))
    class_index: int = int(np.argmax(predictions))

    # Map index to human-readable label
    class_label: str = CLASS_LABELS[class_index]

    logger.info(
        "Prediction: '%s' | confidence: %.4f | above threshold: %s",
        class_label,
        confidence,
        confidence >= CONFIDENCE_THRESHOLD,
    )

    return class_label, confidence