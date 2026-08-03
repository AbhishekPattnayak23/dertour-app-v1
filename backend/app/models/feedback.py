from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class FeedbackType(str, Enum):
    GENERAL = "general"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"

class FeedbackStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class Feedback(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="Reference to the user who submitted feedback")
    type: FeedbackType = Field(default=FeedbackType.GENERAL)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    status: FeedbackStatus = Field(default=FeedbackStatus.PENDING)
    tags: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    admin_notes: Optional[str] = None
    is_anonymous: bool = Field(default=False)
    contact_email: Optional[str] = None
    priority: str = Field(default="medium")
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "user_id": "user123",
                "type": "feature_request",
                "rating": 4,
                "title": "Add dark mode",
                "description": "Would love to see a dark mode option for better night viewing",
                "tags": ["ui", "accessibility"],
                "is_anonymous": False,
                "contact_email": "user@example.com",
                "priority": "medium"
            }
        }
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum of 10 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v.lower() not in valid_priorities:
            raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v.lower()
    
    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "rating": self.rating,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "admin_notes": self.admin_notes,
            "is_anonymous": self.is_anonymous,
            "contact_email": self.contact_email,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feedback":
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        if "reviewed_at" in data and data["reviewed_at"] and isinstance(data["reviewed_at"], str):
            data["reviewed_at"] = datetime.fromisoformat(data["reviewed_at"].replace('Z', '+00:00'))
        return cls(**data)
    
    def mark_as_reviewed(self, reviewed_by: str, admin_notes: Optional[str] = None):
        self.status = FeedbackStatus.REVIEWED
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewed_by
        self.updated_at = datetime.utcnow()
        if admin_notes:
            self.admin_notes = admin_notes
    
    def update_status(self, status: FeedbackStatus, reviewed_by: Optional[str] = None):
        self.status = status
        self.updated_at = datetime.utcnow()
        if reviewed_by:
            self.reviewed_by = reviewed_by
            self.reviewed_at = datetime.utcnow()