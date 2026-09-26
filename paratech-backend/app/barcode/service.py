import os
import uuid

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile


TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)


async def read_uploaded_image(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be an image.",
        )

    content = await file.read()
    image_array = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=422,
            detail="Cannot decode uploaded image.",
        )

    return image


def read_image_from_path(image_path: str):
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail=f"Image not found: {image_path}",
        )

    image = cv2.imread(image_path)

    if image is None:
        raise HTTPException(
            status_code=422,
            detail="Cannot read image file.",
        )

    return image