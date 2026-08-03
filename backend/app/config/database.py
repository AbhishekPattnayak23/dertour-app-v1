"""Database configuration and connection management for Azure SQL and Cosmos DB."""

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, DateTime, Boolean, Text
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from .settings import settings


class AzureSQLConnection:
    """Azure SQL Database connection manager."""

    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.metadata = MetaData()
        self.session_factory = None

    async def connect(self):
        """Establish connection to Azure SQL Database."""
        connection_string = (
            f"mssql+pyodbc://{settings.AZURE_SQL_USERNAME}:"
            f"{settings.AZURE_SQL_PASSWORD}@{settings.AZURE_SQL_SERVER}/"
            f"{settings.AZURE_SQL_DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"
        )

        self.async_engine = create_async_engine(
            connection_string.replace('mssql+pyodbc', 'mssql+aioodbc'),
            echo=settings.DEBUG
        )

        self.session_factory = sessionmaker(
            self.async_engine, class_=AsyncSession
        )

    def create_tables(self):
        """Create database tables."""
        users_table = Table(
            'users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('username', String(50), unique=True, nullable=False),
            Column('email', String(100), unique=True, nullable=False),
            Column('full_name', String(100)),
            Column('is_active', Boolean, default=True),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )

        conversations_table = Table(
            'conversations', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, nullable=False),
            Column('title', String(200)),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )

        messages_table = Table(
            'messages', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('conversation_id', Integer, nullable=False),
            Column('role', String(20), nullable=False),
            Column('content', Text, nullable=False),
            Column('created_at', DateTime)
        )

        return {
            'users': users_table,
            'conversations': conversations_table,
            'messages': messages_table
        }

    async def get_session(self):
        """Get database session."""
        if not self.session_factory:
            await self.connect()
        return self.session_factory()


class CosmosDBConnection:
    """Azure Cosmos DB connection manager."""

    def __init__(self):
        self.client = None
        self.database = None
        self.containers = {}

    async def connect(self):
        """Establish connection to Azure Cosmos DB."""
        self.client = CosmosClient(
            settings.COSMOS_ENDPOINT,
            settings.COSMOS_KEY
        )

        try:
            self.database = await self.client.create_database_if_not_exists(
                id=settings.COSMOS_DATABASE_NAME
            )
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error connecting to Cosmos DB: {e}")
            raise

    async def get_container(self, container_name: str):
        """Get or create container."""
        if container_name not in self.containers:
            try:
                container = await self.database.create_container_if_not_exists(
                    id=container_name,
                    partition_key="/id"
                )
                self.containers[container_name] = container
            except exceptions.CosmosHttpResponseError as e:
                print(f"Error creating container {container_name}: {e}")
                raise

        return self.containers[container_name]

    async def insert_document(self, container_name: str, document: dict):
        """Insert document into container."""
        container = await self.get_container(container_name)
        try:
            return await container.create_item(body=document)
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error inserting document: {e}")
            raise

    async def query_documents(self, container_name: str, query: str):
        """Query documents from container."""
        container = await self.get_container(container_name)
        try:
            items = []
            async for item in container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                items.append(item)
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error querying documents: {e}")
            raise


# Global instances
azure_sql = AzureSQLConnection()
cosmos_db = CosmosDBConnection()


async def get_azure_sql_session():
    """Dependency to get Azure SQL session."""
    session = await azure_sql.get_session()
    try:
        yield session
    finally:
        await session.close()


async def get_cosmos_client():
    """Dependency to get Cosmos DB client."""
    if not cosmos_db.client:
        await cosmos_db.connect()
    return cosmos_db
