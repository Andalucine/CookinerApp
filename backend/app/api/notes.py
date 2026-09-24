"""Notas: free pages of a notebook. Owner and editors write; viewers read."""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Note
from app.schemas.auth import MessageResponse
from app.schemas.note import NoteCreate, NoteIn, NoteOut, NoteSummary
from app.services import note as note_service
from app.services import permissions

router = APIRouter(prefix="/notes", tags=["notes"])


def _summary_fields(note: Note) -> dict:
    return {
        "id": note.id,
        "notebook_id": note.notebook_id,
        "title": note.title,
        "author_id": note.author_id,
        "preview": note_service.preview(note.content),
        "added_by": permissions.added_by(note.notebook, note.author),
        "edited_by": permissions.added_by(note.notebook, note.updated_by),
        "updated_at": note.updated_at,
    }


def _out(note: Note) -> NoteOut:
    return NoteOut(**_summary_fields(note), content=note.content, created_at=note.created_at)


def _notebook(db, user, lang, notebook_id: int | None, *, edit: bool):
    try:
        return permissions.resolve_notebook(db, user, notebook_id, edit=edit)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None


def _load(db, user, lang, note_id: int, *, edit: bool) -> Note:
    try:
        note = note_service.get(db, note_id)
        if edit:
            permissions.require_edit(db, user, note.notebook)
        else:
            permissions.require_view(db, user, note.notebook)
    except (note_service.NoteNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("note_not_found", lang)) from None
    return note


@router.get("", response_model=list[NoteSummary])
def list_notes(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
    q: str | None = Query(default=None, description="Search in title and content"),
) -> list[NoteSummary]:
    notebook = _notebook(db, user, lang, notebook_id, edit=False)
    return [NoteSummary(**_summary_fields(n)) for n in note_service.list_notes(db, notebook.id, q)]


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(body: NoteCreate, db: DbSession, user: CurrentUser, lang: Lang) -> NoteOut:
    """Add a note to your notebook, or to a notebook where you are editor."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    note = note_service.create(db, user, notebook.id, NoteIn(**body.model_dump()))
    return _out(note)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> NoteOut:
    return _out(_load(db, user, lang, note_id, edit=False))


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int, body: NoteIn, db: DbSession, user: CurrentUser, lang: Lang
) -> NoteOut:
    note = _load(db, user, lang, note_id, edit=True)
    return _out(note_service.update(db, note, user, body))


@router.delete("/{note_id}", response_model=MessageResponse)
def delete_note(note_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    """Only the notebook owner or the note's author."""
    note = _load(db, user, lang, note_id, edit=True)
    if not permissions.can_delete(user, note.notebook, note.author_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    note_service.delete(db, note)
    return MessageResponse(message=t("note_deleted", lang))
