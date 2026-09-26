from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    user_id: int
    query: str
    input_data: dict[str, Any]


class RecommendationResponse(BaseModel):
    message: str
    recommended_products: list[dict[str, Any]]


class RecommendationHistoryResponse(BaseModel):
    id: int
    user_id: int
    query: str
    input_data: str
    recommended_products: str
    created_at: datetime