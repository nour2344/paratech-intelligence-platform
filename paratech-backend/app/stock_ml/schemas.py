from typing import Optional

from pydantic import BaseModel


class StockMlPredictRequest(BaseModel):
    StockQuantity: float
    AlertQuantity: float
    avg_daily_sales: float
    stock_coverage: float
    stock_value_ratio: float
    days_to_stockout: float
    StockValue: float
    ProductCategory_enc: int


class StockMlPredictResponse(BaseModel):
    risk_level: str
    alert: bool
    confidence: float


class StockMlAnalyzeRequest(BaseModel):
    product_name: str


class StockMlProductSearchItem(BaseModel):
    product_name: str
    category: Optional[str] = None
    current_stock: float
    alert_threshold: float


class StockMlSearchResponse(BaseModel):
    count: int
    results: list[StockMlProductSearchItem]


class StockMlAlert(BaseModel):
    active: bool
    severity: str
    title: str
    message: str


class StockMlAnalysisResponse(BaseModel):
    product_name: str
    category: Optional[str] = None

    current_stock: float
    alert_threshold: float
    average_daily_sales: float
    estimated_days_before_stockout: float

    risk_level: str
    risk_label: str
    confidence: float

    alert: StockMlAlert
    recommendation: str


class StockMlHealthResponse(BaseModel):
    status: str
    module: str
    model: str
    model_loaded: bool
    model_error: Optional[str] = None
