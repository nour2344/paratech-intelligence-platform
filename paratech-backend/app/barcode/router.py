from fastapi import APIRouter, File, UploadFile

from app.barcode.pipeline import (
    get_pipeline_status,
    load_barcode_pipeline,
    run_barcode_scan,
)
from app.barcode.schemas import BarcodePathRequest, BarcodeScanResponse
from app.barcode.service import read_image_from_path, read_uploaded_image

router = APIRouter()


@router.get("/health")
def barcode_health():
    return get_pipeline_status()


@router.post("/scan", response_model=BarcodeScanResponse)
async def scan_barcode(file: UploadFile = File(...)):
    image = await read_uploaded_image(file)
    return run_barcode_scan(image)


@router.post("/scan/path", response_model=BarcodeScanResponse)
def scan_barcode_from_path(data: BarcodePathRequest):
    image = read_image_from_path(data.image_path)
    return run_barcode_scan(image)