"""
Feedback Repository for managing user feedback data access operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime
import logging
from uuid import UUID, uuid4
from azure.cosmos.aio import ContainerProxy

from ..models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Repository class for feedback data access operations."""

    def __init__(self, db_session: Session = None, container: ContainerProxy = None):
        """Initialize the feedback repository.

        Args:
            db_session: SQLAlchemy database session
            container: Cosmos DB container proxy
        """
        self.db = db_session
        self.container = container

    def create_feedback(self, feedback_data: Dict[str, Any]) -> Feedback:
        """Create a new feedback entry.

        Args:
            feedback_data: Dictionary containing feedback information

        Returns:
            Feedback: Created feedback object

        Raises:
            Exception: If feedback creation fails
        """
        try:
            feedback = Feedback(**feedback_data)
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            logger.info(f"Created feedback with ID: {feedback.id}")
            return feedback
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create feedback: {str(e)}")
            raise

    async def create_feedback_async(self, feedback: FeedbackCreate, user_id: UUID) -> FeedbackResponse:
        """Create new feedback entry in Cosmos DB."""
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

    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            Optional[Feedback]: Feedback object if found, None otherwise
        """
        try:
            feedback = (
                self.db.query(Feedback)
                .filter(Feedback.id == feedback_id)
                .first()
            )
            return feedback
        except Exception as e:
            logger.error(f"Failed to get feedback {feedback_id}: {str(e)}")
            return None

    async def get_feedback_by_id_async(self, feedback_id: str) -> Optional[FeedbackResponse]:
        """Get feedback by ID from Cosmos DB."""
        try:
            item = await self.container.read_item(item=feedback_id, partition_key=feedback_id)
            return FeedbackResponse(**item)
        except Exception:
            return None

    def get_feedbacks_by_user(self, user_id: int,
        limit: int = 100) -> List[Feedback]:
        """Get all feedbacks by a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of feedbacks to return

        Returns:
            List[Feedback]: List of feedback objects
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .filter(Feedback.user_id == user_id)
                .order_by(desc(Feedback.created_at))
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to get feedbacks for user {user_id}: "
                         f"{str(e)}")
            return []

    async def get_user_feedback(self, user_id: UUID, limit: int = 50) -> List[FeedbackResponse]:
        """Get feedback by user ID from Cosmos DB."""
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

    def get_feedbacks_by_query(self, query_id: int,
        limit: int = 100) -> List[Feedback]:
        """Get all feedbacks for a specific query.

        Args:
            query_id: Query ID
            limit: Maximum number of feedbacks to return

        Returns:
            List[Feedback]: List of feedback objects
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .filter(Feedback.query_id == query_id)
                .order_by(desc(Feedback.created_at))
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to get feedbacks for query {query_id}: "
                         f"{str(e)}")
            return []

    def get_feedbacks_by_rating(self, rating: int,
        limit: int = 100) -> List[Feedback]:
        """Get all feedbacks with a specific rating.

        Args:
            rating: Rating value
            limit: Maximum number of feedbacks to return

        Returns:
            List[Feedback]: List of feedback objects
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .filter(Feedback.rating == rating)
                .order_by(desc(Feedback.created_at))
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to get feedbacks with rating {rating}: "
                        f"{str(e)}")
            return []

    def update_feedback(self, feedback_id: int,
        update_data: Dict[str, Any]) -> Optional[Feedback]:
        """Update an existing feedback.

        Args:
            feedback_id: Feedback ID
            update_data: Dictionary containing fields to update

        Returns:
            Optional[Feedback]: Updated feedback object if successful

        Raises:
            Exception: If feedback update fails
        """
        try:
            feedback = (
                self.db.query(Feedback)
                .filter(Feedback.id == feedback_id)
                .first()
            )

            if not feedback:
                logger.warning(f"Feedback {feedback_id} not found for "
                              "update")
                return None

            for key, value in update_data.items():
                if hasattr(feedback, key):
                    setattr(feedback, key, value)

            feedback.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(feedback)

            logger.info(f"Updated feedback {feedback_id}")
            return feedback
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update feedback {feedback_id}: "
                        f"{str(e)}")
            raise

    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete a feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            bool: True if deleted successfully, False otherwise

        Raises:
            Exception: If feedback deletion fails
        """
        try:
            feedback = (
                self.db.query(Feedback)
                .filter(Feedback.id == feedback_id)
                .first()
            )

            if not feedback:
                logger.warning(f"Feedback {feedback_id} not found for "
                              "deletion")
                return False

            self.db.delete(feedback)
            self.db.commit()

            logger.info(f"Deleted feedback {feedback_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete feedback {feedback_id}: "
                        f"{str(e)}")
            raise

    def list(self, limit: int = 100, offset: int = 0):
        """List feedback entries with pagination"""
        try:
            return self.db.query(Feedback).offset(offset).limit(limit).all()
        except Exception as e:
            raise Exception(f"Error listing feedback: {str(e)}")

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics.

        Returns:
            Dict[str, Any]: Dictionary containing feedback statistics
        """
        try:
            total_feedbacks = self.db.query(Feedback).count()

            rating_stats = (
                self.db.query(
                    Feedback.rating,
                        func.count(Feedback.id).label('count')
                )
                .group_by(Feedback.rating)
                .all()
            )

            avg_rating = (
                self.db.query(func.avg(Feedback.rating))
                .scalar()
            )

            return {
                'total_feedbacks': total_feedbacks,
                    'rating_distribution': {
                    str(rating): count for rating, count in rating_stats
                },
                    'average_rating': float(avg_rating) if avg_rating else 0.0
            }
        except Exception as e:
            logger.error(f"Failed to get feedback statistics: {str(e)}")
            return {
                'total_feedbacks': 0,
                    'rating_distribution': {},
                    'average_rating': 0.0
            }

    def get_recent_feedbacks(self, limit: int = 50) -> List[Feedback]:
        """Get recent feedbacks ordered by creation date.

        Args:
            limit: Maximum number of feedbacks to return

        Returns:
            List[Feedback]: List of recent feedback objects
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .order_by(desc(Feedback.created_at))
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to get recent feedbacks: {str(e)}")
            return []

    def search_feedbacks(self, search_term: str,
        limit: int = 100) -> List[Feedback]:
        """Search feedbacks by content.

        Args:
            search_term: Search term to look for in feedback content
            limit: Maximum number of results to return

        Returns:
            List[Feedback]: List of matching feedback objects
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .filter(Feedback.content.ilike(f'%{search_term}%'))
                .order_by(desc(Feedback.created_at))
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to search feedbacks: {str(e)}")
            return []

    def get_feedbacks_by_date_range(self, start_date: datetime,
                                        end_date: datetime,
                                        skip: int = 0, limit: int = 100) -> List[Feedback]:
        """Get feedbacks within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Feedback]: List of feedback objects within date range
        """
        try:
            feedbacks = (
                self.db.query(Feedback)
                .filter(and_(
                    Feedback.created_at >= start_date,
                    Feedback.created_at <= end_date
                ))
                .order_by(desc(Feedback.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
            return feedbacks
        except Exception as e:
            logger.error(f"Failed to get feedbacks by date range: {str(e)}")
            return []
