from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, update, delete, func
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
import logging

T = TypeVar('T')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')

logger = logging.getLogger(__name__)

class BaseRepository(ABC, Generic[T, CreateSchemaType, UpdateSchemaType]):
    """Abstract base repository defining the contract for all repositories."""
    
    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create a new record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Union[str, UUID, int]) -> Optional[T]:
        """Get a record by its ID."""
        pass
    
    @abstractmethod
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple records with pagination and filtering."""
        pass
    
    @abstractmethod
    async def update(self, id: Union[str, UUID, int], obj_in: UpdateSchemaType) -> Optional[T]:
        """Update a record by ID."""
        pass
    
    @abstractmethod
    async def delete(self, id: Union[str, UUID, int]) -> bool:
        """Delete a record by ID."""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        pass

class BaseSQLRepository(BaseRepository[T, CreateSchemaType, UpdateSchemaType]):
    """Base SQL repository with common SQLAlchemy operations."""
    
    def __init__(self, model: type[DeclarativeBase], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session
    
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create a new record in the database."""
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.__dict__
                db_obj = self.model(**obj_data)
            
            self.db_session.add(db_obj)
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
    
    async def get_by_id(self, id: Union[str, UUID, int]) -> Optional[T]:
        """Get a record by its ID."""
        try:
            result = await self.db_session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {str(e)}")
            raise
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple records with pagination and filtering."""
        try:
            query = select(self.model)
            
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, field).in_(value))
                        elif isinstance(value, dict) and 'operator' in value:
                            column = getattr(self.model, field)
                            operator = value['operator']
                            val = value['value']
                            
                            if operator == 'eq':
                                query = query.where(column == val)
                            elif operator == 'ne':
                                query = query.where(column != val)
                            elif operator == 'gt':
                                query = query.where(column > val)
                            elif operator == 'gte':
                                query = query.where(column >= val)
                            elif operator == 'lt':
                                query = query.where(column < val)
                            elif operator == 'lte':
                                query = query.where(column <= val)
                            elif operator == 'like':
                                query = query.where(column.like(f"%{val}%"))
                            elif operator == 'ilike':
                                query = query.where(column.ilike(f"%{val}%"))
                        else:
                            query = query.where(getattr(self.model, field) == value)
            
            query = query.offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {str(e)}")
            raise
    
    async def update(self, id: Union[str, UUID, int], obj_in: UpdateSchemaType) -> Optional[T]:
        """Update a record by ID."""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.__dict__
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                return await self.get_by_id(id)
            
            await self.db_session.execute(
                update(self.model).where(self.model.id == id).values(**update_data)
            )
            await self.db_session.commit()
            return await self.get_by_id(id)
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    async def delete(self, id: Union[str, UUID, int]) -> bool:
        """Delete a record by ID."""
        try:
            result = await self.db_session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error deleting {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        try:
            query = select(func.count(self.model.id))
            
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            query = query.where(getattr(self.model, field).in_(value))
                        else:
                            query = query.where(getattr(self.model, field) == value)
            
            result = await self.db_session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise
    
    async def exists(self, id: Union[str, UUID, int]) -> bool:
        """Check if a record exists by ID."""
        try:
            result = await self.db_session.execute(
                select(func.count(self.model.id)).where(self.model.id == id)
            )
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} with ID {id}: {str(e)}")
            raise

class BaseCosmosRepository(BaseRepository[T, CreateSchemaType, UpdateSchemaType]):
    """Base Cosmos DB repository with common operations."""
    
    def __init__(self, container: ContainerProxy, partition_key: str = "id"):
        self.container = container
        self.partition_key = partition_key
    
    async def create(self, obj_in: CreateSchemaType) -> T:
        """Create a new document in Cosmos DB."""
        try:
            if isinstance(obj_in, dict):
                item_data = obj_in
            else:
                item_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.__dict__
            
            # Ensure id field exists
            if 'id' not in item_data:
                import uuid
                item_data['id'] = str(uuid.uuid4())
            
            response = await self.container.create_item(body=item_data)
            return response
        except Exception as e:
            logger.error(f"Error creating document in Cosmos DB: {str(e)}")
            raise
    
    async def get_by_id(self, id: Union[str, UUID, int]) -> Optional[T]:
        """Get a document by its ID."""
        try:
            response = await self.container.read_item(
                item=str(id), 
                partition_key=str(id)
            )
            return response
        except Exception as e:
            if "NotFound" in str(e):
                return None
            logger.error(f"Error getting document by ID {id}: {str(e)}")
            raise
    
    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple documents with pagination and filtering."""
        try:
            query = "SELECT * FROM c"
            parameters = []
            
            if filters:
                conditions = []
                for i, (field, value) in enumerate(filters.items()):
                    param_name = f"@param{i}"
                    conditions.append(f"c.{field} = {param_name}")
                    parameters.append({"name": param_name, "value": value})
                
                if conditions:
                    query += f" WHERE {' AND '.join(conditions)}"
            
            query += f" OFFSET {skip} LIMIT {limit}"
            
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)
            
            return items
        except Exception as e:
            logger.error(f"Error getting multiple documents: {str(e)}")
            raise
    
    async def update(self, id: Union[str, UUID, int], obj_in: UpdateSchemaType) -> Optional[T]:
        """Update a document by ID."""
        try:
            # First, get the existing document
            existing_item = await self.get_by_id(id)
            if not existing_item:
                return None
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.__dict__
            
            # Update the existing item
            existing_item.update(update_data)
            
            response = await self.container.replace_item(
                item=str(id),
                body=existing_item
            )
            return response
        except Exception as e:
            logger.error(f"Error updating document with ID {id}: {str(e)}")
            raise
    
    async def delete(self, id: Union[str, UUID, int]) -> bool:
        """Delete a document by ID."""
        try:
            await self.container.delete_item(
                item=str(id),
                partition_key=str(id)
            )
            return True
        except Exception as e:
            if "NotFound" in str(e):
                return False
            logger.error(f"Error deleting document with ID {id}: {str(e)}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents with optional filtering."""
        try:
            query = "SELECT VALUE COUNT(1) FROM c"
            parameters = []
            
            if filters:
                conditions = []
                for i, (field, value) in enumerate(filters.items()):
                    param_name = f"@param{i}"
                    conditions.append(f"c.{field} = {param_name}")
                    parameters.append({"name": param_name, "value": value})
                
                if conditions:
                    query += f" WHERE {' AND '.join(conditions)}"
            
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)
            
            return items[0] if items else 0
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            raise