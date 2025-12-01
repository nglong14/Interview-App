from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Cloud Run specific
    environment: str = "development"  # development, production
    
    # Cloud SQL connection (for production)
    cloud_sql_connection_name: str = ""  # Format: project:region:instance

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def database_url(self) -> str:
        #Get database URL based on environment
        
        if self.is_production and self.cloud_sql_connection_name:
            # Use Unix socket for Cloud SQL
            db_url = f"postgresql://{self.database_username}:{self.database_password}@/{self.database_name}?host=/cloudsql/{self.cloud_sql_connection_name}"
            return db_url
        elif self.database_hostname.startswith("/cloudsql/"):
            # Direct Unix socket path provided (alternative method)
            db_url = f"postgresql://{self.database_username}:{self.database_password}@/{self.database_name}?host={self.database_hostname}"
            return db_url
        else:
            # Use TCP for local/development
            db_url = f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"
            return db_url


settings = Settings()