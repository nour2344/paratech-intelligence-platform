from fastapi import APIRouter, Query

from app.stock_ml.schemas import (
    StockMlAnalyzeRequest,
    StockMlAnalysisResponse,
    StockMlHealthResponse,
    StockMlPredictRequest,
    StockMlPredictResponse,
    StockMlSearchResponse,
)
from app.stock_ml.service import (
    analyze_stock_ml_product_service,
    get_model_info_service,
    get_stock_ml_alerts_service,
    is_model_loaded,
    predict_stock_ml_service,
    search_stock_ml_products_service,
)

router = APIRouter()


@router.get("/health", response_model=StockMlHealthResponse)
def stock_ml_health():
    return {
        "status": "ok",
        "module": "stock_shortage_ml",
        "model": "xgboost",
        "model_loaded": is_model_loaded(),
        "model_error": None,
    }


@router.get("/model/info")
def stock_ml_model_info():
    return get_model_info_service()


@router.post("/predict", response_model=StockMlPredictResponse)
def predict_stock_ml(request: StockMlPredictRequest):
    return predict_stock_ml_service(request)


@router.get("/search", response_model=StockMlSearchResponse)
def search_stock_ml_products(
    name: str = Query(..., min_length=2),
):
    return search_stock_ml_products_service(name)


@router.post("/analyze", response_model=StockMlAnalysisResponse)
def analyze_stock_ml_product(request: StockMlAnalyzeRequest):
    return analyze_stock_ml_product_service(request)


@router.get("/alerts", response_model=list[StockMlAnalysisResponse])
def get_stock_ml_alerts():
    return get_stock_ml_alerts_service()
