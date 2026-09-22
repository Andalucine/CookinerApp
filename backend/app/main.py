"""CookinerApp API entry point."""

import logging

from fastapi import FastAPI

from app.api import auth, health
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s")

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="API del recetario compartido CookinerApp.",
)

app.include_router(health.router)
app.include_router(auth.router)
