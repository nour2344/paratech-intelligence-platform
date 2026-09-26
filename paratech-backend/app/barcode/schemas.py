from typing import Any

from pydantic import BaseModel


class BarcodeScanResponse(BaseModel):
    success: bool
    barcode: str | None
    product: dict[str, Any] | None
    recommendations: list[dict[str, Any]]
    error: str | None = None


class BarcodePathRequest(BaseModel):
    image_path: str