from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    #AI provider settings
    ai_provider: str
    ai_api_key: str
    ai_model: str
    ai_max_tokens: int
    ai_temperature: float#controls the randomness/creativity -> higher = more creative

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
