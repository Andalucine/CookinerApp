"""Spices of a notebook (session 8): the notebook's own spices, and its own substitute lists
for any ingredient. Owner and editors change them; owner or creator deletes. The catalogue
itself is read in /spices."""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Ingredient, Notebook, NotebookSpice
from app.schemas.auth import MessageResponse
from app.schemas.spice import (
    NotebookSpiceCreate,
    NotebookSpiceIn,
    NotebookSpiceOut,
    PairingIn,
    SubstitutionOut,
    SubstitutionsIn,
)
from app.services import notebook_spice as spice_service
from app.services import permissions

router = APIRouter(prefix="/notebook-spices", tags=["notebook-spices"])


def _notebook(db, user, lang, notebook_id: int | None, *, edit: bool) -> Notebook:
    try:
        return permissions.resolve_notebook(db, user, notebook_id, edit=edit)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None


def _load_editable(db, user, lang, spice_id: int) -> tuple[NotebookSpice, Notebook]:
    try:
        spice = spice_service.get(db, spice_id)
        notebook = db.get(Notebook, spice.notebook_id)
        permissions.require_edit(db, user, notebook)
    except (spice_service.SpiceNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang)) from None
    return spice, notebook


# --- Own spices --------------------------------------------------------------------------


@router.get("", response_model=list[NotebookSpiceOut])
def list_spices(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> list[NotebookSpiceOut]:
    notebook = _notebook(db, user, lang, notebook_id, edit=False)
    return [spice_service.to_out(s, notebook) for s in spice_service.list_for(db, notebook.id)]


@router.post("", response_model=NotebookSpiceOut, status_code=status.HTTP_201_CREATED)
def create_spice(
    body: NotebookSpiceCreate, db: DbSession, user: CurrentUser, lang: Lang
) -> NotebookSpiceOut:
    """A spice of the notebook, in one of the seven families."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    try:
        spice = spice_service.create(db, user, notebook, body)
    except spice_service.SpiceExists:
        raise HTTPException(status.HTTP_409_CONFLICT, t("spice_exists", lang)) from None
    return spice_service.to_out(spice, notebook)


@router.put("/{spice_id}", response_model=NotebookSpiceOut)
def update_spice(
    spice_id: int, body: NotebookSpiceIn, db: DbSession, user: CurrentUser, lang: Lang
) -> NotebookSpiceOut:
    spice, notebook = _load_editable(db, user, lang, spice_id)
    try:
        spice = spice_service.update(db, spice, body)
    except spice_service.SpiceExists:
        raise HTTPException(status.HTTP_409_CONFLICT, t("spice_exists", lang)) from None
    return spice_service.to_out(spice, notebook)


@router.delete("/{spice_id}", response_model=MessageResponse)
def delete_spice(spice_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    """Only the notebook owner or whoever added it."""
    spice, notebook = _load_editable(db, user, lang, spice_id)
    if not permissions.can_delete(user, notebook, spice.created_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    spice_service.delete_spice(db, spice)
    return MessageResponse(message=t("spice_deleted", lang))


# --- Own substitute lists ------------------------------------------------------------------


@router.put("/{ingredient_id}/substitutions", response_model=list[SubstitutionOut])
def set_substitutions(
    ingredient_id: int, body: SubstitutionsIn, db: DbSession, user: CurrentUser, lang: Lang
) -> list[SubstitutionOut]:
    """The notebook's list of substitutes for this ingredient (catalogue spice or its own).
    It replaces the catalogue's list for the notebook."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang))
    try:
        rows = spice_service.set_substitutions(db, user, notebook, ingredient, body.items)
    except spice_service.SelfSubstitute:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("substitute_self", lang)
        ) from None
    return [spice_service.substitution_out(r, None) for r in rows]


@router.delete("/{ingredient_id}/substitutions", response_model=MessageResponse)
def clear_substitutions(
    ingredient_id: int,
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> MessageResponse:
    """Back to the catalogue's list."""
    notebook = _notebook(db, user, lang, notebook_id, edit=True)
    if not spice_service.clear_substitutions(db, notebook.id, ingredient_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang))
    return MessageResponse(message=t("substitutions_restored", lang))


# --- Own "va bien con" -------------------------------------------------------------------


@router.put("/{ingredient_id}/pairs-with", response_model=MessageResponse)
def set_pairing(
    ingredient_id: int, body: PairingIn, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    """The notebook's "va bien con" for this ingredient; replaces the catalogue's text."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang))
    spice_service.set_pairing(db, user, notebook, ingredient, body.pairs_with)
    return MessageResponse(message=t("ok", lang))


@router.delete("/{ingredient_id}/pairs-with", response_model=MessageResponse)
def clear_pairing(
    ingredient_id: int,
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> MessageResponse:
    """Back to the catalogue's text."""
    notebook = _notebook(db, user, lang, notebook_id, edit=True)
    if not spice_service.clear_pairing(db, notebook.id, ingredient_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("spice_not_found", lang))
    return MessageResponse(message=t("ok", lang))
