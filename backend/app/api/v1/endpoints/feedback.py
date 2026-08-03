from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class FeedbackCreate(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}

    @validator("rating")
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class FeedbackResponse(BaseModel):
    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    rating: Optional[int]
    comment: Optional[str]
    category: Optional[str]
    tags: List[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime


class RatingSummary(BaseModel):
    resource_id: str
    resource_type: Optional[str]
    total_ratings: int
    average_rating: float
    rating_distribution: dict
    total_comments: int


in_memory_feedback_store: dict = {}


def get_feedback_store():
    return in_memory_feedback_store


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback: FeedbackCreate,
    store: dict = Depends(get_feedback_store),
):
    feedback_id = str(uuid4())
    now = datetime.utcnow()

    feedback_record = {
        "id": feedback_id,
        "user_id": feedback.user_id,
        "session_id": feedback.session_id,
        "resource_id": feedback.resource_id,
        "resource_type": feedback.resource_type,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "category": feedback.category,
        "tags": feedback.tags or [],
        "metadata": feedback.metadata or {},
        "created_at": now,
        "updated_at": now,
    }

    store[feedback_id] = feedback_record
    logger.info(f"Created feedback with id={feedback_id}")
    return FeedbackResponse(**feedback_record)


@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    user_id: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: dict = Depends(get_feedback_store),
):
    results = list(store.values())

    if user_id:
        results = [r for r in results if r.get("user_id") == user_id]
    if resource_id:
        results = [r for r in results if r.get("resource_id") == resource_id]
    if resource_type:
        results = [r for r in results if r.get("resource_type") == resource_type]
    if category:
        results = [r for r in results if r.get("category") == category]
    if min_rating is not None:
        results = [r for r in results if r.get("rating") is not None and r["rating"] >= min_rating]
    if max_rating is not None:
        results = [r for r in results if r.get("rating") is not None and r["rating"] <= max_rating]

    results.sort(key=lambda x: x["created_at"], reverse=True)
    paginated = results[offset: offset + limit]

    return [FeedbackResponse(**r) for r in paginated]


@router.get("/summary", response_model=RatingSummary)
async def get_rating_summary(
    resource_id: str = Query(...),
    resource_type: Optional[str] = Query(None),
    store: dict = Depends(get_feedback_store),
):
    results = [
        r for r in store.values()
        if r.get("resource_id") == resource_id
    ]

    if resource_type:
        results = [r for r in results if r.get("resource_type") == resource_type]

    if not results:
        raise HTTPException(status_code=404, detail="No feedback found for the given resource")

    ratings = [r["rating"] for r in results if r.get("rating") is not None]
    comments = [r for r in results if r.get("comment")]

    distribution = {str(i): 0 for i in range(1, 6)}
    for rating in ratings:
        distribution[str(rating)] = distribution.get(str(rating), 0) + 1

    average = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    return RatingSummary(
        resource_id=resource_id,
        resource_type=resource_type,
        total_ratings=len(ratings),
        average_rating=average,
        rating_distribution=distribution,
        total_comments=len(comments),
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    store: dict = Depends(get_feedback_store),
):
    record = store.get(feedback_id)
    if not record:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return FeedbackResponse(**record)


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    updates: FeedbackUpdate,
    store: dict = Depends(get_feedback_store),
):
    record = store.get(feedback_id)
    if not record:
        raise HTTPException(status_code=404, detail="Feedback not found")

    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        record[key] = value

    record["updated_at"] = datetime.utcnow()
    store[feedback_id] = record

    logger.info(f"Updated feedback id={feedback_id}")
    return FeedbackResponse(**record)


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(
    feedback_id: str,
    store: dict = Depends(get_feedback_store),
):
    if feedback_id not in store:
        raise HTTPException(status_code=404, detail="Feedback not found")

    del store[feedback_id]
    logger.info(f"Deleted feedback id={feedback_id}")
    return None


@router.post("/{feedback_id}/rate", response_model=FeedbackResponse)
async def rate_feedback(
    feedback_id: str,
    rating: int = Query(..., ge=1, le=5),
    store: dict = Depends(get_feedback_store),
):
    record = store.get(feedback_id)
    if not record:
        raise HTTPException(status_code=404, detail="Feedback not found")

    record["rating"] = rating
    record["updated_at"] = datetime.utcnow()
    store[feedback_id] = record

    logger.info(f"Rated feedback id={feedback_id} with rating={rating}")
    return FeedbackResponse(**record)

@router.post("/rating", response_model=dict)
async def submit_rating(
    rating_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Submit user rating and comments."""
    return {"message": "Rating/comment endpoint", "data": rating_data}
