"""CookinerApp API entry point."""

import logging

from fastapi import FastAPI

from app.api import (
    auth,
    blends,
    catalog,
    health,
    imports,
    menus,
    notebook_spices,
    notebooks,
    notes,
    occasions,
    pantry,
    photos,
    recipes,
    shopping_list,
    spices,
    wines,
)
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s")

app = FastAPI(
    title=settings.app_name,
    version="0.8.0",
    description="API de CookinerApp, el cuaderno de cocina personal.",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(notebooks.router)
app.include_router(catalog.router)
app.include_router(recipes.router)
app.include_router(pantry.router)
app.include_router(shopping_list.router)
app.include_router(spices.router)
app.include_router(blends.router)
app.include_router(notebook_spices.router)
app.include_router(notes.router)
app.include_router(wines.router)
app.include_router(occasions.router)
app.include_router(imports.router)
app.include_router(photos.router)
app.include_router(menus.router)
