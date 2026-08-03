from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

Base = declarative_base()

class EnquiryTicket(Base):
    __tablename__ = 'enquiry_tickets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='open')
    priority = Column(String(20), nullable=False, default='medium')
    category = Column(String(50), nullable=True)
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_active': self.is_active
        }

class Conversation:
    def __init__(self, conversation_id: str = None, user_id: str = None, title: str = None, 
                 created_at: datetime = None, updated_at: datetime = None, 
                 is_active: bool = True, metadata: Dict[str, Any] = None):
        self.id = conversation_id or str(uuid.uuid4())
        self.conversation_id = self.id
        self.user_id = user_id
        self.title = title or "New Conversation"
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
        self.metadata = metadata or {}
        self.partition_key = user_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'is_active': self.is_active,
            'metadata': self.metadata,
            'partition_key': self.partition_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
        return cls(
            conversation_id=data.get('id') or data.get('conversation_id'),
            user_id=data.get('user_id'),
            title=data.get('title'),
            created_at=created_at,
            updated_at=updated_at,
            is_active=data.get('is_active', True),
            metadata=data.get('metadata', {})
        )

class Message:
    def __init__(self, message_id: str = None, conversation_id: str = None, 
                 user_id: str = None, content: str = None, message_type: str = 'user',
                 timestamp: datetime = None, metadata: Dict[str, Any] = None,
                 is_deleted: bool = False):
        self.id = message_id or str(uuid.uuid4())
        self.message_id = self.id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.content = content or ""
        self.message_type = message_type
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
        self.is_deleted = is_deleted
        self.partition_key = conversation_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'message_id': self.message_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'content': self.content,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'metadata': self.metadata,
            'is_deleted': self.is_deleted,
            'partition_key': self.partition_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        timestamp = data.get('timestamp')
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
        return cls(
            message_id=data.get('id') or data.get('message_id'),
            conversation_id=data.get('conversation_id'),
            user_id=data.get('user_id'),
            content=data.get('content'),
            message_type=data.get('message_type', 'user'),
            timestamp=timestamp,
            metadata=data.get('metadata', {}),
            is_deleted=data.get('is_deleted', False)
        )