from fastapi import APIRouter

from app.demand.schemas import (
    ForecastByNameRequest,
    ForecastRequest,
    ForecastResponse,
)
from app.demand.service import (
    forecast_demand_by_name_service,
    forecast_demand_service,
    get_forecastable_products,
)

router = APIRouter()


@router.get("/health")
def demand_health():
    return {
        "status": "ok",
        "module": "demand_forecasting",
        "model": "xgboost",
        "model_ready": True,
    }


@router.get("/products")
def list_forecastable_products():
    """
    Returns only products that exist in both:
    - dimProducts.csv
    - factSales.csv

    These are the products that can be used for demand forecasting.
    """
    return get_forecastable_products()


@router.post("/forecast", response_model=ForecastResponse)
def forecast_demand(request: ForecastRequest):
    return forecast_demand_service(
        product_id=request.product_id,
        horizon=request.horizon,
    )


@router.post("/forecast/by-name", response_model=ForecastResponse)
def forecast_demand_by_name(request: ForecastByNameRequest):
    return forecast_demand_by_name_service(
        product_name=request.product_name,
        horizon=request.horizon,
    )


@router.post("/predict", response_model=ForecastResponse)
def predict(request: ForecastRequest):
    return forecast_demand(request)


@router.post("/predict/batch")
def predict_batch(requests: list[ForecastRequest]):
    return [forecast_demand(request) for request in requests]


@router.post("/retrain")
def retrain():
    return {
        "status": "success",
        "message": "Retraining triggered successfully.",
    }


@router.post("/simulate/drift")
def simulate_drift():
    return {
        "status": "success",
        "message": "Demand forecasting drift simulated.",
    }


@router.post("/simulate/reset")
def reset_simulation():
    return {
        "status": "success",
        "message": "Demand forecasting simulation reset.",
    }