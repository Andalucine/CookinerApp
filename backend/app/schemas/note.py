"""Free notes of a notebook."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# The same values as app.models.note.NOTE_KINDS (session 9)
NoteKind = Literal["recipes", "wines", "spices", "celebrations", "shopping", "ideas"]


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str | None = None
    kind: NoteKind | None = None


class NoteCreate(NoteIn):
    notebook_id: int | None = Field(
        default=None, description="Notebook to add the note to; your own if omitted"
    )


class NoteSummary(BaseModel):
    id: int
    notebook_id: int
    title: str
    kind: NoteKind | None = None
    author_id: int | None = None  # who wrote it: the app offers Borrar to the owner and to them
    preview: str | None = None  # first 140 characters of the content
    added_by: str | None = None  # "(añadido por NOMBRE)" when the author is not the owner
    edited_by: str | None = None  # "(editado por NOMBRE)" when the last editor is not the owner
    updated_at: datetime


class NoteOut(NoteSummary):
    content: str | None = None
    created_at: datetime
