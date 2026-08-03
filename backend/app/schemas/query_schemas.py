from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    user_id: str = Field(..., description="ID of the user creating the conversation")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional conversation metadata")


class ConversationResponse(BaseModel):
    id: str = Field(..., description="Unique conversation identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    user_id: str = Field(..., description="ID of the conversation owner")
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, description="Conversation status")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages in conversation")
    metadata: dict = Field(default_factory=dict, description="Additional conversation metadata")

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    conversation_id: str = Field(..., description="ID of the conversation this message belongs to")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    message_type: MessageType = Field(default=MessageType.USER, description="Type of message")
    user_id: Optional[str] = Field(None, description="ID of the user sending the message")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional message metadata")


class MessageResponse(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="ID of the conversation")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    user_id: Optional[str] = Field(None, description="ID of the user who sent the message")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional message metadata")

    class Config:
        from_attributes = True


class EnquiryTicketCreate(BaseModel):
    subject: str = Field(..., min_length=5, max_length=255, description="Ticket subject")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of the enquiry")
    user_id: str = Field(..., description="ID of the user creating the ticket")
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, description="Ticket priority level")
    category: Optional[str] = Field(None, max_length=100, description="Ticket category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the ticket")
    contact_email: Optional[str] = Field(None, description="Contact email for follow-up")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional ticket metadata")