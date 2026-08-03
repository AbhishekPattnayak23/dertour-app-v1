"""Application settings and configuration management."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "Dertour Travel Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"

    # Azure SQL Database
    AZURE_SQL_SERVER: str = "your-server.database.windows.net"
    AZURE_SQL_DATABASE: str = "travel_agent"
    AZURE_SQL_USERNAME: str = "admin"
    AZURE_SQL_PASSWORD: str = "your-password"

    # Azure Cosmos DB
    COSMOS_ENDPOINT: str = "https://your-cosmos.documents.azure.com:443/"
    COSMOS_KEY: str = "your-cosmos-key"
    COSMOS_DATABASE_NAME: str = "travel_agent_nosql"

    # Azure AD
    AZURE_AD_TENANT_ID: str = "your-tenant-id"
    AZURE_AD_CLIENT_ID: str = "your-client-id"
    AZURE_AD_CLIENT_SECRET: str = "your-client-secret"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000"
    ]

    class Config:
        env_file = ".env"


settings = Settings()
