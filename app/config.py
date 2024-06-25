import os

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine


class Settings(BaseSettings):
    """
    Settings for the application, loaded from environment variables with defaults.

    Attributes:
        database_url (str): The URL for the PostgreSQL database.
        redis_host (str): The host address for Redis.
        redis_port (int): The port number for Redis.
        rate_limit_times (int): The maximum number of requests allowed within the rate limit period.
        rate_limit_seconds (int): The period for rate limiting in seconds.
    """

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db/claims"
    )
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    rate_limit_times: int = int(os.getenv("RATE_LIMIT_TIMES", 10))
    rate_limit_seconds: int = int(os.getenv("RATE_LIMIT_SECONDS", 60))


settings = Settings()

engine = create_async_engine(settings.database_url, echo=True)
"""
SQLAlchemy asynchronous engine instance configured with the database URL from settings.
"""
