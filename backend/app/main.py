"""CookinerApp API entry point."""

from fastapi import FastAPI

from app.api import health
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API del recetario compartido CookinerApp.",
)

app.include_router(health.router)
