"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CookinerApp API"
    app_env: str = "development"
    secret_key: str = "change-me"
    default_language: str = "es"
    database_url: str = "postgresql+psycopg://cookiner:cookiner@localhost:5432/cookinerapp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
