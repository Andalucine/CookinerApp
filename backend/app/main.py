"""CookinerApp API entry point."""

import logging

from fastapi import FastAPI

from app.api import auth, catalog, health, notebooks, pantry, recipes, shopping_list
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s")

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="API de CookinerApp, el cuaderno de cocina personal.",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(notebooks.router)
app.include_router(catalog.router)
app.include_router(recipes.router)
app.include_router(pantry.router)
app.include_router(shopping_list.router)
