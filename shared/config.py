from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(...)
    redis_url: str = Field(...)
    sendgrid_api_key: str = Field(default="")
    jwt_secret: str = Field(default="dev-secret-change-me-in-production")

    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7

    h1_api_username: str = Field(default="")
    h1_api_token: str = Field(default="")
    bugcrowd_api_token: str = Field(default="")
    intigriti_api_token: str = Field(default="")

    poll_interval_minutes: int = 60
    recon_worker_concurrency: int = 2
    subprocess_timeout_seconds: int = 300
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
