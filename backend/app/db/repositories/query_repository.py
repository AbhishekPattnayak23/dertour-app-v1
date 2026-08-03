"""Query repository for Cosmos DB operations."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from azure.cosmos.aio import ContainerProxy
from app.schemas.chat import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse


class QueryRepository:
    """Repository for conversation and message operations in Cosmos DB."""

    def __init__(self, container: ContainerProxy):
        self.container = container

    async def create_conversation(self, conversation: ConversationCreate, user_id: UUID) -> ConversationResponse:
        """Create new conversation."""
        conv_item = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "title": conversation.title,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "type": "conversation"
        }

        created_item = await self.container.create_item(conv_item)
        return ConversationResponse(**created_item)

    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get conversation by ID."""
        try:
            item = await self.container.read_item(item=conversation_id, partition_key=conversation_id)
            if item.get("type") == "conversation":
                return ConversationResponse(**item)
        except Exception:
            pass
        return None

    async def create_message(self, message: MessageCreate, conversation_id: str, user_id: UUID) -> MessageResponse:
        """Create new message."""
        msg_item = {
            "id": str(uuid4()),
            "conversation_id": conversation_id,
            "user_id": str(user_id),
            "content": message.content,
            "role": message.role,
            "created_at": datetime.utcnow().isoformat(),
            "type": "message"
        }

        created_item = await self.container.create_item(msg_item)
        return MessageResponse(**created_item)

    async def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[MessageResponse]:
        """Get messages for a conversation."""
        query = "SELECT * FROM c WHERE c.conversation_id = @conversation_id AND c.type = 'message' ORDER BY c.created_at ASC"
        parameters = [{"name": "@conversation_id", "value": conversation_id}]

        items = []
        async for item in self.container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=limit
        ):
            items.append(MessageResponse(**item))

        return items
