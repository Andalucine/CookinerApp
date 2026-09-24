"""Blends of a notebook (session 8): create, change and remove the notebook's own blends and
its versions of catalogue blends. Owner and editors may change; owner or creator may delete.
The catalogue itself is read in /spices."""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Notebook, NotebookBlend
from app.schemas.auth import MessageResponse
from app.schemas.spice import BlendCreate, BlendIn, BlendOut
from app.services import blend as blend_service
from app.services import permissions

router = APIRouter(prefix="/blends", tags=["blends"])


def _notebook(db, user, lang, notebook_id: int | None, *, edit: bool) -> Notebook:
    try:
        return permissions.resolve_notebook(db, user, notebook_id, edit=edit)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None


def _load_editable(db, user, lang, blend_id: int) -> tuple[NotebookBlend, Notebook]:
    try:
        blend = blend_service.get(db, blend_id)
        notebook = db.get(Notebook, blend.notebook_id)
        permissions.require_edit(db, user, notebook)
    except (blend_service.BlendNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("blend_not_found", lang)) from None
    return blend, notebook


def _save(action, lang):
    try:
        return action()
    except blend_service.BlendExists:
        raise HTTPException(status.HTTP_409_CONFLICT, t("blend_exists", lang)) from None
    except blend_service.BlendSameIngredient:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("blend_same_ingredient", lang)
        ) from None


@router.get("", response_model=list[BlendOut])
def list_blends(
    db: DbSession,
    user: CurrentUser,
    lang: Lang,
    notebook_id: int | None = Query(default=None, description="Default: your own notebook"),
) -> list[BlendOut]:
    """The notebook's blends: its own and its versions of catalogue blends."""
    notebook = _notebook(db, user, lang, notebook_id, edit=False)
    return [blend_service.to_out(b, notebook) for b in blend_service.list_for(db, notebook.id)]


@router.post("", response_model=BlendOut, status_code=status.HTTP_201_CREATED)
def create_blend(body: BlendCreate, db: DbSession, user: CurrentUser, lang: Lang) -> BlendOut:
    """A new blend, or the notebook's version of a catalogue blend (same name)."""
    notebook = _notebook(db, user, lang, body.notebook_id, edit=True)
    blend = _save(lambda: blend_service.create(db, user, notebook, body), lang)
    return blend_service.to_out(blend, notebook)


@router.put("/{blend_id}", response_model=BlendOut)
def update_blend(
    blend_id: int, body: BlendIn, db: DbSession, user: CurrentUser, lang: Lang
) -> BlendOut:
    blend, notebook = _load_editable(db, user, lang, blend_id)
    blend = _save(lambda: blend_service.update(db, blend, body), lang)
    return blend_service.to_out(blend, notebook)


@router.delete("/{blend_id}", response_model=MessageResponse)
def delete_blend(blend_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    """Only the notebook owner or whoever created it. A version of a catalogue blend goes back
    to the catalogue's."""
    blend, notebook = _load_editable(db, user, lang, blend_id)
    if not permissions.can_delete(user, notebook, blend.created_by_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("forbidden", lang))
    blend_service.delete(db, blend)
    return MessageResponse(message=t("blend_deleted", lang))
