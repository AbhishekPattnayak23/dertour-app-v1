"""Feedback repository for Cosmos DB operations."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from azure.cosmos.aio import ContainerProxy
from app.schemas.feedback import FeedbackCreate, FeedbackResponse


class FeedbackRepository:
    """Repository for feedback operations in Cosmos DB."""

    def __init__(self, container: ContainerProxy):
        self.container = container

    async def create_feedback(self, feedback: FeedbackCreate, user_id: UUID) -> FeedbackResponse:
        """Create new feedback entry."""
        feedback_item = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        created_item = await self.container.create_item(feedback_item)
        return FeedbackResponse(**created_item)

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackResponse]:
        """Get feedback by ID."""
        try:
            item = await self.container.read_item(item=feedback_id, partition_key=feedback_id)
            return FeedbackResponse(**item)
        except Exception:
            return None

    async def get_user_feedback(self, user_id: UUID, limit: int = 50) -> List[FeedbackResponse]:
        """Get feedback by user ID."""
        query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC"
        parameters = [{"name": "@user_id", "value": str(user_id)}]

        items = []
        async for item in self.container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=limit
        ):
            items.append(FeedbackResponse(**item))

        return items
