"""Importing a recipe from a web page: the request, the editable preview and the history."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.recipe import RecipeIn


class RecipeImportRequest(BaseModel):
    url: str = Field(min_length=8, max_length=1000)
    notebook_id: int | None = Field(
        default=None, description="Notebook to import into; your own if omitted"
    )


class RecipeImportPreview(BaseModel):
    """What the app shows before saving. `recipe` is ready to send back (edited or not) to
    POST /imports/{job_id}/save."""

    job_id: int
    notebook_id: int
    complete: bool  # False: the page had no recipe data, only title and photo
    warnings: list[str] = []
    recipe: RecipeIn


class ImportJobOut(BaseModel):
    id: int
    kind: str
    url: str
    status: str  # pending | ok | error
    error_message: str | None = None
    recipe_id: int | None = None
    created_at: datetime
    finished_at: datetime | None = None
