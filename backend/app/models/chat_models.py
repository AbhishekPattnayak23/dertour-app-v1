from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class EventType(str, Enum):
    MESSAGE_START = "message_start"
    MESSAGE_CHUNK = "message_chunk"
    MESSAGE_END = "message_end"
    ERROR = "error"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CLOSED = "connection_closed"


class ChatMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    type: MessageType
    content: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    token_count: Optional[int] = Field(None, ge=0)
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ChatConversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: Optional[str] = Field(None, max_length=200)
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    total_tokens: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
    
    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        if message.token_count:
            self.total_tokens += message.token_count
    
    def get_messages_by_type(self, message_type: MessageType) -> List[ChatMessage]:
        return [msg for msg in self.messages if msg.type == message_type]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ChatEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: EventType
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    retry: Optional[int] = Field(None, ge=0)
    
    def to_sse_format(self) -> str:
        lines = []
        
        if self.id:
            lines.append(f"id: {self.id}")
        
        lines.append(f"event: {self.type.value}")
        
        if self.data:
            import json
            lines.append(f"data: {json.dumps(self.data, default=str)}")
        else:
            lines.append("data: {}")
        
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def message_chunk(cls, content: str, conversation_id: UUID, message_id: UUID) -> "ChatEvent":
        return cls(
            type=EventType.MESSAGE_CHUNK,
            data={"content": content},
            conversation_id=conversation_id,
            message_id=message_id
        )
    
    @classmethod
    def message_start(cls, conversation_id: UUID, message_id: UUID) -> "ChatEvent":
        return cls(
            type=EventType.MESSAGE_START,
            data={"message_id": str(message_id)},
            conversation_id=conversation_id,
            message_id=message_id
        )
    
    @classmethod
    def message_end(cls, conversation_id: UUID, message_id: UUID, token_count: Optional[int] = None) -> "ChatEvent":
        data = {"message_id": str(message_id)}
        if token_count is not None:
            data["token_count"] = token_count
        
        return cls(
            type=EventType.MESSAGE_END,
            data=data,
            conversation_id=conversation_id,
            message_id=message_id
        )
    
    @classmethod
    def error(cls, error_message: str, conversation_id: Optional[UUID] = None) -> "ChatEvent":
        return cls(
            type=EventType.ERROR,
            data={"error": error_message},
            conversation_id=conversation_id
        )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }