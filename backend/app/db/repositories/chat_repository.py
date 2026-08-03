from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.database import DatabaseProxy

from app.models.chat import Chat, Message
from app.core.config import settings


class ChatRepository:
    def __init__(self, cosmos_client: CosmosClient):
        self.client = cosmos_client
        self.database: DatabaseProxy = self.client.get_database_client(settings.COSMOS_DATABASE_NAME)
        self.container: ContainerProxy = self.database.get_container_client("chats")

    async def create_chat(self, user_id: str, title: str = None) -> Chat:
        """Create a new chat conversation"""
        chat_id = str(uuid.uuid4())
        chat_data = {
            "id": chat_id,
            "user_id": user_id,
            "title": title or "New Chat",
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_archived": False
        }
        
        try:
            created_item = self.container.create_item(body=chat_data)
            return Chat(**created_item)
        except exceptions.CosmosResourceExistsError:
            raise ValueError(f"Chat with id {chat_id} already exists")
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to create chat: {e.message}")

    async def get_chat_by_id(self, chat_id: str, user_id: str) -> Optional[Chat]:
        """Get a chat by ID for a specific user"""
        try:
            item = self.container.read_item(item=chat_id, partition_key=user_id)
            return Chat(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to get chat: {e.message}")

    async def get_chats_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Chat]:
        """Get all chats for a user with pagination"""
        try:
            query = """
            SELECT * FROM c 
            WHERE c.user_id = @user_id AND c.is_archived = false
            ORDER BY c.updated_at DESC
            OFFSET @offset LIMIT @limit
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [Chat(**item) for item in items]
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to get user chats: {e.message}")

    async def update_chat(self, chat_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Chat]:
        """Update chat properties"""
        try:
            existing_chat = self.container.read_item(item=chat_id, partition_key=user_id)
            
            # Update allowed fields
            allowed_updates = {"title", "is_archived"}
            for key, value in updates.items():
                if key in allowed_updates:
                    existing_chat[key] = value
            
            existing_chat["updated_at"] = datetime.utcnow().isoformat()
            
            updated_item = self.container.replace_item(
                item=chat_id,
                body=existing_chat
            )
            
            return Chat(**updated_item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to update chat: {e.message}")

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat (soft delete by archiving)"""
        try:
            return await self.update_chat(chat_id, user_id, {"is_archived": True}) is not None
        except Exception:
            return False

    async def add_message(self, chat_id: str, user_id: str, message: Message) -> Optional[Chat]:
        """Add a message to a chat"""
        try:
            existing_chat = self.container.read_item(item=chat_id, partition_key=user_id)
            
            message_dict = {
                "id": str(uuid.uuid4()),
                "role": message.role,
                "content": message.content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": message.metadata or {}
            }
            
            existing_chat["messages"].append(message_dict)
            existing_chat["updated_at"] = datetime.utcnow().isoformat()
            
            updated_item = self.container.replace_item(
                item=chat_id,
                body=existing_chat
            )
            
            return Chat(**updated_item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to add message: {e.message}")

    async def get_messages(self, chat_id: str, user_id: str, limit: int = 100) -> List[Message]:
        """Get messages from a chat"""
        try:
            chat = await self.get_chat_by_id(chat_id, user_id)
            if not chat:
                return []
            
            messages = chat.messages[-limit:] if limit else chat.messages
            return [Message(**msg) for msg in messages]
        except Exception as e:
            raise Exception(f"Failed to get messages: {str(e)}")

    async def search_chats(self, user_id: str, query: str, limit: int = 20) -> List[Chat]:
        """Search chats by title or message content"""
        try:
            search_query = """
            SELECT * FROM c 
            WHERE c.user_id = @user_id 
            AND c.is_archived = false
            AND (CONTAINS(LOWER(c.title), LOWER(@query))
                OR EXISTS(SELECT VALUE m FROM m IN c.messages 
                         WHERE CONTAINS(LOWER(m.content), LOWER(@query))))
            ORDER BY c.updated_at DESC
            OFFSET 0 LIMIT @limit
            """
            
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@query", "value": query},
                {"name": "@limit", "value": limit}
            ]
            
            items = list(self.container.query_items(
                query=search_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [Chat(**item) for item in items]
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to search chats: {e.message}")

    async def get_chat_count(self, user_id: str) -> int:
        """Get total number of active chats for a user"""
        try:
            query = """
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.user_id = @user_id AND c.is_archived = false
            """
            parameters = [{"name": "@user_id", "value": user_id}]
            
            result = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return result[0] if result else 0
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to get chat count: {e.message}")