import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from threading import Lock
import redis
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    id: str
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    max_messages: int = 50

    def add_message(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        message = Message(
            id=str(uuid.uuid4()),
            content=content,
            role=role,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Trim messages if exceeding max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        return message

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        return self.messages[-count:] if self.messages else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'max_messages': self.max_messages
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        messages = [Message.from_dict(msg_data) for msg_data in data.get('messages', [])]
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            messages=messages,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata'),
            max_messages=data.get('max_messages', 50)
        )

class ConversationManager:
    def __init__(self, redis_client: Optional[redis.Redis] = None, session_timeout: int = 3600):
        self.redis_client = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.session_timeout = session_timeout  # seconds
        self.lock = Lock()
        self._session_prefix = "chat:session:"
        self._user_sessions_prefix = "chat:user_sessions:"

    def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        with self.lock:
            # Store session context
            self._store_context(context)
            
            # Add session to user's session list
            user_sessions_key = f"{self._user_sessions_prefix}{user_id}"
            self.redis_client.sadd(user_sessions_key, session_id)
            self.redis_client.expire(user_sessions_key, self.session_timeout * 24)  # Keep user sessions longer
        
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve a conversation session"""
        session_key = f"{self._session_prefix}{session_id}"
        
        try:
            session_data = self.redis_client.get(session_key)
            if session_data:
                context = ConversationContext.from_dict(json.loads(session_data))
                return context
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error deserializing session {session_id}: {e}")
            return None

    def add_message(self, session_id: str, content: str, role: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Message]:
        """Add a message to a conversation session"""
        with self.lock:
            context = self.get_session(session_id)
            if not context:
                logger.warning(f"Session {session_id} not found")
                return None
            
            message = context.add_message(content, role, metadata)
            self._store_context(context)
            
            logger.debug(f"Added message to session {session_id}: {message.id}")
            return message

    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Message]:
        """Get conversation history for a session"""
        context = self.get_session(session_id)
        if not context:
            return []
        
        return context.get_recent_messages(limit)

    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata"""
        with self.lock:
            context = self.get_session(session_id)
            if not context:
                return False
            
            if context.metadata:
                context.metadata.update(metadata)
            else:
                context.metadata = metadata
            
            context.updated_at = datetime.utcnow()
            self._store_context(context)
            return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        with self.lock:
            context = self.get_session(session_id)
            if not context:
                return False
            
            # Remove from Redis
            session_key = f"{self._session_prefix}{session_id}"
            user_sessions_key = f"{self._user_sessions_prefix}{context.user_id}"
            
            self.redis_client.delete(session_key)
            self.redis_client.srem(user_sessions_key, session_id)
            
            logger.info(f"Deleted session {session_id}")
            return True

    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        user_sessions_key = f"{self._user_sessions_prefix}{user_id}"
        sessions = self.redis_client.smembers(user_sessions_key)
        
        # Filter out expired sessions
        valid_sessions = []
        for session_id in sessions:
            if self.get_session(session_id):
                valid_sessions.append(session_id)
            else:
                # Clean up invalid session reference
                self.redis_client.srem(user_sessions_key, session_id)
        
        return valid_sessions

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (should be run periodically)"""
        # This is handled automatically by Redis TTL, but we can implement
        # additional cleanup logic here if needed
        cleaned_count = 0
        
        # Get all session keys
        session_pattern = f"{self._session_prefix}*"
        session_keys = self.redis_client.keys(session_pattern)
        
        for session_key in session_keys:
            ttl = self.redis_client.ttl(session_key)
            if ttl == -2:  # Key doesn't exist
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count

    def extend_session_timeout(self, session_id: str) -> bool:
        """Extend the timeout for a session"""
        session_key = f"{self._session_prefix}{session_id}"
        if self.redis_client.exists(session_key):
            self.redis_client.expire(session_key, self.session_timeout)
            return True
        return False

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session"""
        context = self.get_session(session_id)
        if not context:
            return None
        
        user_messages = [msg for msg in context.messages if msg.role == 'user']
        assistant_messages = [msg for msg in context.messages if msg.role == 'assistant']
        
        return {
            'session_id': session_id,
            'user_id': context.user_id,
            'total_messages': len(context.messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat(),
            'duration_minutes': (context.updated_at - context.created_at).total_seconds() / 60
        }

    def _store_context(self, context: ConversationContext):
        """Store conversation context in Redis"""
        session_key = f"{self._session_prefix}{context.session_id}"
        context_data = json.dumps(context.to_dict(), ensure_ascii=False)
        
        self.redis_client.setex(
            session_key,
            self.session_timeout,
            context_data
        )

    def health_check(self) -> bool:
        """Check if the conversation manager is healthy"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False