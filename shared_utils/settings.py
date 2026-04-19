from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType


class Settings(BaseSettings):
    
        
    API_PORT: int = 8080
    BACKEND_URL: str = "http://localhost:8080"
        
    
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    RUN_MIGRATIONS: bool = False
    
    
    
    APP_URL: str
    
    APP_NAME: str
    AWS_ACCOUNT_ID: Optional[str] = None
    AWS_REGION: str
    ENVIRONMENT: str = "local"
    REPO: str
    SENTRY_DSN: Optional[str] = None
    AUTH_API_URL: Optional[str] = None
    AUTH_API_REQUEST_TIMEOUT: Optional[int] = 5
    EXECUTION_ENVIRONMENT: ExecutionEnvironmentType = ExecutionEnvironmentType.LOCAL if ENVIRONMENT.lower() in ["local", "test"] else ExecutionEnvironmentType.FARGATE
    LOGGING_FORMAT: LogOutputFormat =  LogOutputFormat.TEXT if ENVIRONMENT.lower() in ["local", "test"] else LogOutputFormat.JSON
    LOG_LEVEL: Optional[str] = "info"

    # Uncomment the below to run alembic commands locally, or to run the db interface independently of fastapi
    # from pydantic_settings import SettingsConfigDict
    if ENVIRONMENT == "local":
        model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_logger(level: str | None = None) -> StructuredLogger:
    return StructuredLogger(
        level=level or "info",
        options={
            "execution_environment": get_settings().EXECUTION_ENVIRONMENT,
            "log_format": get_settings().LOGGING_FORMAT,
        },
    )
