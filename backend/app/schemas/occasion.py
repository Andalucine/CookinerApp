"""A notebook's own occasions (épocas propias), next to the preloaded ones."""

from pydantic import BaseModel, Field

from app.schemas.catalog import OccasionOut


class OccasionIn(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="As the user writes it")


class OccasionCreate(OccasionIn):
    notebook_id: int | None = Field(
        default=None, description="Notebook to add the occasion to; your own if omitted"
    )


class NotebookOccasionOut(OccasionOut):
    notebook_id: int | None = None  # None for the preloaded ones
    added_by: str | None = None  # "(añadido por NOMBRE)" when not the notebook owner
