# /home/mohith/Catchup-Mohith/backend/app/core/config.py
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # Redis
    redis_url: str
    redis_cache_db: int = 0
    redis_auth_db: int = 1

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Auth rate limiting
    auth_rate_limit_attempts: int = 5
    auth_rate_limit_window_seconds: int = 900

    # Temporal
    temporal_host: str = "temporal-server"
    temporal_port: int = 7233
    temporal_namespace: str = "default"
    temporal_db: str = "temporal"
    temporal_task_queue: str = "stockbridge-main"

    # Admin seed
    initial_admin_email: str = "admin@stockbridge.local"
    initial_admin_password: str = "REDACTED_SEE_ENV"

    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    sendgrid_sandbox_mode: bool = True

    # Application
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # pgAdmin
    REDACTED_SEE_ENV_default_email: str = "admin@stockbridge.local"
    REDACTED_SEE_ENV_default_password: str = "REDACTED_SEE_ENV"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def redis_cache_url(self) -> str:
        return f"{self.redis_url.rstrip('/')}/{self.redis_cache_db}"

    @property
    def redis_auth_url(self) -> str:
        return f"{self.redis_url.rstrip('/')}/{self.redis_auth_db}"


settings = Settings()
