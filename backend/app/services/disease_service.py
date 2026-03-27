"""
app/services/disease_service.py

Loads diseases.json once at module import time and exposes
a single lookup function used by the prediction router.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Resolve path relative to this file so it works regardless of where
# uvicorn is launched from.
_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "diseases.json"

# --- Load JSON into memory once ---
try:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        _DISEASE_DB: dict = json.load(f)
    logger.info("Disease database loaded: %d entries", len(_DISEASE_DB))
except FileNotFoundError:
    logger.error("diseases.json not found at %s", _DATA_PATH)
    _DISEASE_DB = {}


# Fallback record shown when the predicted class has no entry in the DB
_UNKNOWN_RECORD = {
    "display_name": "Unknown Disease",
    "symptoms": "No symptom data available for this classification.",
    "cure": "Please consult a local agricultural extension office for advice.",
}


def get_disease_info(class_label: str) -> dict:
    """
    Return the disease record for a given model class label.

    Args:
        class_label: Raw output class name from the model
                     (e.g. 'Tomato___Late_blight').

    Returns:
        dict with keys: display_name, symptoms, cure.
        Falls back to _UNKNOWN_RECORD if the label is not in the database.
    """
    record = _DISEASE_DB.get(class_label)

    if record is None:
        logger.warning("No disease record found for class label: '%s'", class_label)
        return _UNKNOWN_RECORD

    return record