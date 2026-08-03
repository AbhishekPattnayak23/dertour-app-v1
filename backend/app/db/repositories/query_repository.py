from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from app.db.models.query import Query, Conversation
from app.core.exceptions import DatabaseError


class QueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, query_data: Dict[str, Any]) -> Query:
        try:
            query = Query(**query_data)
            self.session.add(query)
            await self.session.commit()
            await self.session.refresh(query)
            return query
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create query: {str(e)}")

    async def get_by_id(self, conversation_id: uuid.UUID) -> Optional[Query]:
        try:
            stmt = select(Query).where(Query.id == conversation_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get query by id: {str(e)}")

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[uuid.UUID] = None,
        conversation_id: Optional[uuid.UUID] = None
    ) -> List[Query]:
        try:
            stmt = select(Query)

            if user_id:
                stmt = stmt.where(Query.user_id == user_id)

            if conversation_id:
                stmt = stmt.where(Query.conversation_id == conversation_id)

            stmt = stmt.order_by(desc(Query.created_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get queries: {str(e)}")

    async def update(self, conversation_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[Query]:
        try:
            stmt = (
                update(Query)
                .where(Query.id == conversation_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await self.session.execute(stmt)
            await self.session.commit()

            return await self.get_by_id(conversation_id)
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update query: {str(e)}")

    async def delete(self, conversation_id: uuid.UUID) -> bool:
        pass

    def list(self, limit: int = 100, offset: int = 0):
        """List queries with pagination"""
        try:
            return self.db.query(Query).offset(offset).limit(limit).all()
        except Exception as e:
            raise Exception(f"Error listing queries: {str(e)}")
        try:
            stmt = delete(Query).where(Query.id == conversation_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete query: {str(e)}")

    def find(self, **kwargs):
        """Find queries by criteria"""
        try:
            query = self.db.query(Query)
            for key, value in kwargs.items():
                if hasattr(Query, key):
                    query = query.filter(getattr(Query, key) == value)
            return query.all()
        except Exception as e:
            raise Exception(f"Error finding queries: {str(e)}")

    async def search(
        self,
        search_term: str,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Query]:
        try:
            stmt = select(Query).where(
                or_(
                    Query.question.ilike(f"%{search_term}%"),
                    Query.response.ilike(f"%{search_term}%")
                )
            )

            if user_id:
                stmt = stmt.where(Query.user_id == user_id)

            stmt = stmt.order_by(desc(Query.created_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to search queries: {str(e)}")

    async def get_by_user_and_timeframe(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Query]:
        try:
            stmt = select(Query).where(
                and_(
                    Query.user_id == user_id,
                    Query.created_at >= start_date,
                    Query.created_at <= end_date
                )
            ).order_by(desc(Query.created_at))

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get queries by timeframe: {str(e)}")

    async def get_recent_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Query]:
        try:
            stmt = (
                select(Query)
                .where(Query.user_id == user_id)
                .order_by(desc(Query.created_at))
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get recent queries: {str(e)}")

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        try:
            stmt = select(func.count(Query.id)).where(Query.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count queries: {str(e)}")


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_data: Dict[str, Any]) -> Conversation:
        try:
            conversation = Conversation(**conversation_data)
            self.session.add(conversation)
            await self.session.commit()
            await self.session.refresh(conversation)
            return conversation
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create conversation: {str(e)}")

    async def get_by_id(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.queries))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get conversation by id: {str(e)}")

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Conversation]:
        try:
            stmt = select(Conversation)

            if user_id:
                stmt = stmt.where(Conversation.user_id == user_id)

            stmt = stmt.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get conversations: {str(e)}")

    async def get_with_queries(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.queries))
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()
            return conversation
        except Exception as e:
            raise DatabaseError(f"Failed to get conversation with queries: {str(e)}")

    async def update(
        self,
        conversation_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Conversation]:
        try:
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await self.session.execute(stmt)
            await self.session.commit()

            return await self.get_by_id(conversation_id)
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update conversation: {str(e)}")

    async def delete(self, conversation_id: uuid.UUID) -> bool:

        pass  # TODO: Implement
        """List queries with pagination"""
        try:
            return self.db.query(Query).offset(offset).limit(limit).all()
        except Exception as e:
            raise Exception(f"Error listing queries: {str(e)}")
        try:
            stmt = delete(Conversation).where(Conversation.id == conversation_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete conversation: {str(e)}")

    def find(self, **kwargs):
        """Find queries by criteria"""
        try:
            query = self.db.query(Query)
            for key, value in kwargs.items():
                if hasattr(Query, key):
                    query = query.filter(getattr(Query, key) == value)
            return query.all()
        except Exception as e:
            raise Exception(f"Error finding queries: {str(e)}")
    async def get_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(Conversation.updated_at))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get conversations by user: {str(e)}")

    async def search(
        self,
        search_term: str,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        try:
            stmt = select(Conversation).where(
                Conversation.title.ilike(f"%{search_term}%")
            )

            if user_id:
                stmt = stmt.where(Conversation.user_id == user_id)

            stmt = stmt.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to search conversations: {str(e)}")

    async def update_last_activity(self, conversation_id: uuid.UUID) -> bool:
        try:
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update conversation activity: {str(e)}")

    async def get_recent_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Conversation]:
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"Failed to get recent conversations: {str(e)}")

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        try:
            stmt = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count conversations: {str(e)}")