from pydantic import BaseModel


class ForecastRequest(BaseModel):
    product_id: int
    horizon: int = 30


class ForecastByNameRequest(BaseModel):
    product_name: str
    horizon: int = 30


class ForecastMetricResponse(BaseModel):
    mae: float
    rmse: float
    r2: float


class ForecastRowResponse(BaseModel):
    date: str
    predicted_quantity: float


class ForecastResponse(BaseModel):
    product_id: int
    product_name: str | None = None
    model: str
    horizon: int
    metrics: ForecastMetricResponse
    forecast: list[ForecastRowResponse]