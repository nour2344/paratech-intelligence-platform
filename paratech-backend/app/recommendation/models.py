from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RecommendationHistory(SQLModel, table=True):
    __tablename__ = "recommendation_history"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    query: str
    input_data: str
    recommended_products: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))