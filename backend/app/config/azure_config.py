import os
import logging
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class AzureConfig:
    """Azure configuration settings."""

    # Storage Account
    storage_account_name: str
    storage_account_key: str
    storage_connection_string: str
    blob_container_name: str

    # Azure Search/Cognitive Search
    search_service_name: str
    search_admin_key: str
    search_query_key: Optional[str]
    search_endpoint: str
    search_index_name: str
    search_api_version: str

    # Azure Cognitive Services
    cognitive_services_key: Optional[str]
    cognitive_services_endpoint: Optional[str]
    cognitive_services_region: Optional[str]

    # Azure SQL Database
    sql_server: Optional[str]
    sql_database: Optional[str]
    sql_username: Optional[str]
    sql_password: Optional[str]
    sql_connection_string: Optional[str]

    # Service Bus
    service_bus_connection_string: Optional[str]
    service_bus_queue_name: Optional[str]

    # Key Vault
    key_vault_name: Optional[str]
    key_vault_url: Optional[str]

    # Application Insights
    application_insights_key: Optional[str]
    application_insights_connection_string: Optional[str]

    # Azure AD
    tenant_id: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]

    # Environment
    environment: str

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._set_derived_fields()

    def _validate_required_fields(self):
        """Validate that required fields are present."""
        required_fields = [
            'storage_account_name',
            'storage_account_key',
            'search_service_name',
            'search_admin_key'
        ]

        missing_fields = []
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or value.strip() == "":
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required Azure configuration fields: {', '.join(missing_fields)}")

    def _set_derived_fields(self):
        """Set derived configuration fields."""
        if not self.storage_connection_string:
            self.storage_connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.storage_account_name};"
                f"AccountKey={self.storage_account_key};"
                f"EndpointSuffix=core.windows.net"
            )

        if not self.search_endpoint:
            self.search_endpoint = f"https://{self.search_service_name}.search.windows.net"

        if self.key_vault_name and not self.key_vault_url:
            self.key_vault_url = f"https://{self.key_vault_name}.vault.azure.net/"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ['production', 'prod']

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ['development', 'dev', 'local']

    def get_search_headers(self) -> dict:
        """Get headers for Azure Search requests."""
        return {
            'Content-Type': 'application/json',
            'api-key': self.search_admin_key
        }

    def get_sql_connection_string(self) -> Optional[str]:
        """Get SQL Server connection string."""
        if self.sql_connection_string:
            return self.sql_connection_string

        if all([self.sql_server, self.sql_database, self.sql_username, self.sql_password]):
            return (
                f"mssql+pyodbc://{self.sql_username}:{self.sql_password}"
                f"@{self.sql_server}/{self.sql_database}"
                f"?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
            )

        return None


def _load_azure_config() -> AzureConfig:
    """Load Azure configuration from environment variables."""

    # Get environment
    environment = os.getenv('ENVIRONMENT', 'development')

    # Storage configuration
    storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', '')
    storage_account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY', '')
    storage_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
    blob_container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME', 'uploads')

    # Search configuration
    search_service_name = os.getenv('AZURE_SEARCH_SERVICE_NAME', '')
    search_admin_key = os.getenv('AZURE_SEARCH_ADMIN_KEY', '')
    search_query_key = os.getenv('AZURE_SEARCH_QUERY_KEY')
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    search_index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'default-index')
    search_api_version = os.getenv('AZURE_SEARCH_API_VERSION', '2023-11-01')

    # Cognitive Services
    cognitive_services_key = os.getenv('AZURE_COGNITIVE_SERVICES_KEY')
    cognitive_services_endpoint = os.getenv('AZURE_COGNITIVE_SERVICES_ENDPOINT')
    cognitive_services_region = os.getenv('AZURE_COGNITIVE_SERVICES_REGION')

    # SQL Database
    sql_server = os.getenv('AZURE_SQL_SERVER')
    sql_database = os.getenv('AZURE_SQL_DATABASE')
    sql_username = os.getenv('AZURE_SQL_USERNAME')
    sql_password = os.getenv('AZURE_SQL_PASSWORD')
    sql_connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')

    # Service Bus
    service_bus_connection_string = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
    service_bus_queue_name = os.getenv('AZURE_SERVICE_BUS_QUEUE_NAME')

    # Key Vault
    key_vault_name = os.getenv('AZURE_KEY_VAULT_NAME')
    key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')

    # Application Insights
    application_insights_key = os.getenv('AZURE_APPLICATION_INSIGHTS_KEY')
    application_insights_connection_string = os.getenv('AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING')

    # Azure AD
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')

    try:
        config = AzureConfig(
            storage_account_name=storage_account_name,
            storage_account_key=storage_account_key,
            storage_connection_string=storage_connection_string,
            blob_container_name=blob_container_name,
            search_service_name=search_service_name,
            search_admin_key=search_admin_key,
            search_query_key=search_query_key,
            search_endpoint=search_endpoint,
            search_index_name=search_index_name,
            search_api_version=search_api_version,
            cognitive_services_key=cognitive_services_key,
            cognitive_services_endpoint=cognitive_services_endpoint,
            cognitive_services_region=cognitive_services_region,
            sql_server=sql_server,
            sql_database=sql_database,
            sql_username=sql_username,
            sql_password=sql_password,
            sql_connection_string=sql_connection_string,
            service_bus_connection_string=service_bus_connection_string,
            service_bus_queue_name=service_bus_queue_name,
            key_vault_name=key_vault_name,
            key_vault_url=key_vault_url,
            application_insights_key=application_insights_key,
            application_insights_connection_string=application_insights_connection_string,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            environment=environment
        )

        logger.info(f"Azure configuration loaded successfully for environment: {environment}")
        return config

    except ValueError as e:
        logger.error(f"Failed to load Azure configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading Azure configuration: {e}")
        raise ValueError(f"Failed to initialize Azure configuration: {e}")


@lru_cache(maxsize=1)
def get_azure_config() -> AzureConfig:
    """Get cached Azure configuration instance."""
    return _load_azure_config()

# ------------------------------------------------------------------
# Azure AI Search Configuration
# ------------------------------------------------------------------

class AzureSearchConfig:
    """Configuration settings for Azure AI Search service."""

    # Azure AI Search Endpoint Configuration
    SEARCH_ENDPOINT = os.getenv(
        "AZURE_SEARCH_ENDPOINT",
        "https://your-search-service.search.windows.net"
    )

    # API Key/Credential Configuration
    SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
    SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY", "")

    # Search Service Configuration
    SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "knowledge-index")
    SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION", "2023-11-01")

    # Vector Search Configuration for Hybrid Search
    VECTOR_DIMENSIONS = int(os.getenv("AZURE_SEARCH_VECTOR_DIMENSIONS", "1536"))
    VECTOR_ALGORITHM = os.getenv("AZURE_SEARCH_VECTOR_ALGORITHM", "hnsw")

    @classmethod
    def get_search_endpoint(cls) -> str:
        """Get the Azure AI Search service endpoint URL."""
        return cls.SEARCH_ENDPOINT

    @classmethod
    def get_search_credentials(cls) -> Dict[str, str]:
        """Get Azure AI Search authentication credentials."""
        return {
            "api_key": cls.SEARCH_API_KEY,
            "admin_key": cls.SEARCH_ADMIN_KEY
        }

    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """Get complete Azure AI Search configuration."""
        return {
            "endpoint": cls.SEARCH_ENDPOINT,
            "api_key": cls.SEARCH_API_KEY,
            "index_name": cls.SEARCH_INDEX_NAME,
            "api_version": cls.SEARCH_API_VERSION,
            "vector_dimensions": cls.VECTOR_DIMENSIONS,
            "vector_algorithm": cls.VECTOR_ALGORITHM
        }

# Export Azure Search configuration instance
azure_search_config = AzureSearchConfig()
