"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CookinerApp API"
    app_env: str = "development"
    secret_key: str = "cambia-esta-clave-por-una-larga-y-aleatoria-de-al-menos-32-caracteres"
    default_language: str = "es"
    database_url: str = "postgresql+psycopg://cookiner:cookiner@localhost:5432/cookinerapp"
    access_token_expire_minutes: int = 60 * 24 * 30  # 30 días: la app móvil no pide login a diario
    password_reset_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
