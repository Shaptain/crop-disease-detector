"""
app/utils/image_utils.py

Image preprocessing utilities.
Converts a raw uploaded file into a normalised numpy array
ready for MobileNetV2 inference.
"""

import io
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, UploadFile

# MobileNetV2 expects 224×224 RGB input
TARGET_SIZE = (224, 224)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def read_and_preprocess(file: UploadFile) -> np.ndarray:
    """
    Read an uploaded image file and return a preprocessed numpy array.

    Steps:
      1. Validate content type and file size.
      2. Decode bytes → PIL Image (RGB).
      3. Resize to TARGET_SIZE.
      4. Normalise pixel values to [0, 1].
      5. Add batch dimension → shape (1, 224, 224, 3).

    Raises:
      HTTPException 400 — invalid file type or unreadable image.
      HTTPException 413 — file exceeds size limit.
    """

    # --- 1. Validate content type ---
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Please upload a JPEG or PNG image.",
        )

    # --- 2. Read raw bytes ---
    raw_bytes = await file.read()

    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 10 MB.",
        )

    # --- 3. Decode to PIL Image ---
    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Could not read image. The file may be corrupted.",
        )

    # --- 4. Resize ---
    image = image.resize(TARGET_SIZE, Image.LANCZOS)

    # --- 5. Normalise and add batch dimension ---
    img_array = np.array(image, dtype=np.float32) / 255.0  # shape: (224, 224, 3)
    img_array = np.expand_dims(img_array, axis=0)           # shape: (1, 224, 224, 3)

    return img_array