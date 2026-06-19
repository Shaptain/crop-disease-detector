"""
app/services/model_service.py

Loads the trained VGG16 PyTorch model ONCE at module import time
and exposes a predict() function used by the prediction router.
"""

import json
import logging
from pathlib import Path
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Minimum softmax probability to trust a prediction.
CONFIDENCE_THRESHOLD = 0.60

# Paths
_MODEL_DIR = Path(__file__).resolve().parents[2] / "model"
_MODEL_PATH = _MODEL_DIR / "plant_disease_model.pth"
_LABELS_PATH = _MODEL_DIR / "class_labels.json"

# ---------------------------------------------------------------------------
# Load class labels
# ---------------------------------------------------------------------------
CLASS_LABELS = []
try:
    if _LABELS_PATH.exists():
        with open(_LABELS_PATH, "r") as f:
            CLASS_LABELS = json.load(f)
        logger.info("Loaded %d class labels from %s", len(CLASS_LABELS), _LABELS_PATH)
    else:
        logger.warning("class_labels.json not found at %s", _LABELS_PATH)
except Exception as e:
    logger.error("Failed to load class labels: %s", e)

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
_model = None

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms

    # Preprocessing pipeline — must match training transforms
    _preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    if _MODEL_PATH.exists() and CLASS_LABELS:
        logger.info("Loading PyTorch model from %s ...", _MODEL_PATH)
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Rebuild VGG16 architecture with custom classifier
        _model = models.vgg16(weights=None)
        _model.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, len(CLASS_LABELS)),
        )

        # Load full model weights (backbone + classifier)
        checkpoint = torch.load(str(_MODEL_PATH), map_location=_device, weights_only=True)
        _model.load_state_dict(checkpoint["model_state_dict"])
        _model = _model.to(_device)
        _model.eval()

        logger.info("Model loaded successfully on %s.", _device)
    else:
        if not _MODEL_PATH.exists():
            logger.warning(
                "Model file not found at %s. "
                "Place your trained .pth file there before sending predictions.",
                _MODEL_PATH,
            )
except ImportError:
    logger.error("PyTorch is not installed. Install it with: pip install torch torchvision")


def is_model_loaded() -> bool:
    """Return True if the model is in memory and ready."""
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
            "Model is not loaded. Check that plant_disease_model.pth "
            "and class_labels.json exist in the model/ directory."
        )

    # img_array comes in as (1, 224, 224, 3) float32 [0,1] from image_utils
    # Convert to uint8 for ToPILImage, then apply PyTorch transforms
    img = (img_array[0] * 255).astype(np.uint8)  # (224, 224, 3)
    tensor = _preprocess(img).unsqueeze(0).to(_device)  # (1, 3, 224, 224)

    with torch.no_grad():
        outputs = _model(tensor)
        probabilities = torch.softmax(outputs, dim=1)

    confidence = float(probabilities.max().item())
    class_index = int(probabilities.argmax().item())
    class_label = CLASS_LABELS[class_index]

    logger.info(
        "Prediction: '%s' | confidence: %.4f | above threshold: %s",
        class_label,
        confidence,
        confidence >= CONFIDENCE_THRESHOLD,
    )

    return class_label, confidence
