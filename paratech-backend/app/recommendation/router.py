from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import engine

from app.recommendation.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.recommendation.service import (
    get_all_recommendation_history_service,
    get_user_recommendation_history_service,
    predict_recommendation_service,
)

router = APIRouter()


@router.post("/predict", response_model=RecommendationResponse)
def predict_recommendation(request: RecommendationRequest):
    return predict_recommendation_service(request)


@router.get("/history/user/{user_id}")
def get_user_recommendation_history(user_id: int):
    return get_user_recommendation_history_service(user_id)


@router.get("/history")
def get_all_recommendation_history():
    return get_all_recommendation_history_service()


class DeleteHistoryBatchRequest(BaseModel):
    ids: list[int]


@router.delete("/history/{history_id}")
def delete_recommendation_history(history_id: int):
    from app.recommendation.models import RecommendationHistory

    with Session(engine) as session:
        history_item = session.get(RecommendationHistory, history_id)

        if not history_item:
            raise HTTPException(status_code=404, detail="History item not found")

        session.delete(history_item)
        session.commit()

    return {
        "status": "success",
        "message": "Recommendation history deleted successfully",
        "deleted_id": history_id,
    }


@router.post("/history/delete-batch")
def delete_recommendation_history_batch(request: DeleteHistoryBatchRequest):
    from app.recommendation.models import RecommendationHistory

    deleted_ids: list[int] = []

    with Session(engine) as session:
        for history_id in request.ids:
            history_item = session.get(RecommendationHistory, history_id)

            if history_item:
                session.delete(history_item)
                deleted_ids.append(history_id)

        session.commit()

    return {
        "status": "success",
        "message": "Recommendation histories deleted successfully",
        "deleted_ids": deleted_ids,
        "deleted_count": len(deleted_ids),
    }