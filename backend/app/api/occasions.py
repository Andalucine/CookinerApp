"""Épocas: the preloaded ones plus the notebook's own (owner and editors add them).

The preloaded list alone is also in /catalog/occasions. A recipe can only use preloaded
occasions or those of its own notebook.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Notebook, Occasion
from app.schemas.auth import MessageResponse
from app.schemas.occasion import NotebookOccasionOut, OccasionCreate, OccasionIn
from app.services import occasion as occasion_service
from app.services import permissions

router = APIRouter(prefix="/occasions", tags=["occasions"])


def _out(occasion: Occasion, notebook: Notebook | None) -> NotebookOccasionOut:
    return NotebookOccasionOut(
        id=occasion.id,
        name_es=occasion.name_es,
        name_en=occasion.name_en,
        is_preloaded=occasion.is_preloaded,
        notebook_id=occasion.notebook_id,
        added_by=permissions.added_by(notebook, occasion.created_by) if notebook else None,
    )


def _notebook(db, user, lang, notebook_id: int | None, *, edit: bool) -> Notebook:
    try:
        return permissions.resolve_notebook(db, user, notebook_id, edit=edit)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None


def _load_own(db, user, lang, occasion_id: int) -> tuple[Occasion, Notebook]:
    """An occasion the user may change: 403 for preloaded ones, 404 without edit access."""
    try:
        occasion = occasion_service.get(db, occasion_id)
    except occasion_service.OccasionNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("occasion_not_found", lang)) from None
    if occasion.notebook_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("occasion_preloaded", lang))
    notebook = db.get(Notebook, occasion.notebook_id)
    try:
        permissions.require_edit(db, user, notebook)
    except permissions.Forbidden:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("occasion_not_found", lang)) from None
    return occasion, notebook


@router.get("", response_model=list[NotebookOccasionOut])
def list_occasions(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> list[NotebookOccasionOut]:
    """Preloaded occasions first, then the notebook's own in alphabetical order."""
    notebook = _notebook(db, user, lang, notebook_id, edit=False)
    return [_out(o, notebook) for o in occasion_service.list_for(db, notebook.id)]


@router.post("", response_model=NotebookOccasionOut, status_code=status.HTTP_201_CREATED)
def create_occasion(
    body: OccasionCreate, db: DbSession, user: CurrentUser, lang: Lang
) -> NotebookOccasionOut:
    """Add an occasion to your notebook ("Cumpleaños de la abuela", "Romería")."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    try:
        occasion = occasion_service.create(db, user, notebook, body.name)
    except occasion_service.OccasionExists:
        raise HTTPException(status.HTTP_409_CONFLICT, t("occasion_exists", lang)) from None
    return _out(occasion, notebook)


@router.put("/{occasion_id}", response_model=NotebookOccasionOut)
def rename_occasion(
    occasion_id: int, body: OccasionIn, db: DbSession, user: CurrentUser, lang: Lang
) -> NotebookOccasionOut:
    occasion, notebook = _load_own(db, user, lang, occasion_id)
    try:
        occasion = occasion_service.rename(db, occasion, body.name)
    except occasion_service.OccasionExists:
        raise HTTPException(status.HTTP_409_CONFLICT, t("occasion_exists", lang)) from None
    return _out(occasion, notebook)


@router.delete("/{occasion_id}", response_model=MessageResponse)
def delete_occasion(
    occasion_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    """Only the notebook owner or whoever created it. Recipes stay; they lose the occasion."""
    occasion, notebook = _load_own(db, user, lang, occasion_id)
    if not permissions.can_delete(user, notebook, occasion.created_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    occasion_service.delete(db, occasion)
    return MessageResponse(message=t("occasion_deleted", lang))
