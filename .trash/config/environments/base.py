from pydantic import BaseModel, Field
from typing import Optional


class DatabaseConfig(BaseModel):
    engine: str = "django.db.backends.postgresql"
    name: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: int = 5432


class OtelConfig(BaseModel):
    grpc_endpoint: str = "localhost:4317"
    http_endpoint: str = "localhost:4318"


class SecurityConfig(BaseModel):
    secret_key: str
    debug: bool = True
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "[::1]"]
    )


class DeploymentConfig(BaseModel):
    id: str = "2f92ca37"
    environment: str = "dev"
