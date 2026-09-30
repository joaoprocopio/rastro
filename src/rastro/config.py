from datetime import timedelta
from functools import cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

CSV = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    """Runtime configuration, read from `RASTRO_*` environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_prefix="RASTRO_",
        env_file=".env",
        extra="ignore",
        frozen=True,
    )

    # signs the CSRF tokens; no default, so a deploy without a secret fails at startup
    secret_key: SecretStr = Field(min_length=32)
    debug: bool = False

    allowed_hosts: CSV = ["localhost", "127.0.0.1", "[::1]"]
    csrf_trusted_origins: CSV = ["http://localhost:8000"]

    postgres_db: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("postgres")
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Sync views run on AnyIO's thread pool, which caps at 40 threads per worker.
    # pool_size + max_overflow bounds the connections of one worker process, so
    # workers * (pool_size + max_overflow) must stay under Postgres' max_connections.
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_timeout: timedelta = timedelta(seconds=30)
    database_pool_recycle: timedelta = timedelta(hours=1)

    # OWASP Session Management: 15 to 30 minutes of idle time for low-risk apps
    session_idle_timeout: timedelta = timedelta(minutes=30)
    session_absolute_timeout: timedelta = timedelta(hours=12)
    # Browsers drop a Secure cookie over plain HTTP, except on localhost.
    cookie_secure: bool = True

    @field_validator("allowed_hosts", "csrf_trusted_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@cache
def get_settings() -> Settings:
    # `model_validate` reads the environment like `Settings()` does, and type
    # checkers accept it without the required `secret_key` argument.
    return Settings.model_validate({})


SettingsDep = Annotated[Settings, Depends(get_settings)]
