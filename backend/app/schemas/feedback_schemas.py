from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"


class FeedbackCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Feedback title")
    content: str = Field(..., min_length=10, max_length=2000, description="Feedback content")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    user_email: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    severity: Optional[Literal["low", "medium", "high", "critical"]] = Field("medium", description="Feedback severity")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "title": "App crashes on login",
                "content": "The application crashes consistently when I try to log in with my credentials.",
                "feedback_type": "bug",
                "user_email": "user@example.com",
                "severity": "high"
            }
        }


class FeedbackResponse(BaseModel):
    id: int
    title: str
    content: str
    feedback_type: str
    user_email: Optional[str]
    severity: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    admin_response: Optional[str] = None
    response_date: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "id": 1,
                "title": "App crashes on login",
                "content": "The application crashes consistently when I try to log in with my credentials.",
                "feedback_type": "bug",
                "user_email": "user@example.com",
                "severity": "high",
                "status": "pending",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
                "admin_response": None,
                "response_date": None
            }
        }


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")
    category: Optional[str] = Field(None, max_length=100, description="Rating category")
    user_email: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @validator('comment')
    def validate_comment(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    class Config:
        schema_extra = {
            "example": {
                "rating": 4,
                "comment": "Great app overall, but could use some UI improvements",
                "category": "user_experience",
                "user_email": "user@example.com"
            }
        }