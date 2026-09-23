"""My notebook and sharing it: invitations by code, accesses, roles, joining and leaving."""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.schemas.auth import MessageResponse
from app.schemas.notebook import (
    AccessOut,
    InvitationCreate,
    InvitationOut,
    JoinRequest,
    NotebookOut,
    NotebookRename,
    RoleChange,
    SharedNotebookOut,
)
from app.schemas.recipe import AuthorOut
from app.services import permissions, sharing
from app.services import recipe as recipe_service

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


def _notebook_out(db, notebook) -> NotebookOut:
    return NotebookOut(
        id=notebook.id,
        name=notebook.name,
        owner=AuthorOut.model_validate(notebook.owner),
        recipe_count=recipe_service.count_in_notebook(db, notebook.id),
        shared_with=sharing.shared_with_count(db, notebook.id),
        max_shared_with=notebook.owner.max_shared_with,
    )


def _access_out(access) -> AccessOut:
    return AccessOut(
        user=AuthorOut.model_validate(access.user), role=access.role, granted_at=access.granted_at
    )


# --- My notebook ----------------------------------------------------------------------------


@router.get("/mine", response_model=NotebookOut)
def my_notebook(db: DbSession, user: CurrentUser) -> NotebookOut:
    return _notebook_out(db, user.notebook)


@router.patch("/mine", response_model=NotebookOut)
def rename_my_notebook(body: NotebookRename, db: DbSession, user: CurrentUser) -> NotebookOut:
    user.notebook.name = body.name.strip()
    db.commit()
    return _notebook_out(db, user.notebook)


@router.get("/shared-with-me", response_model=list[SharedNotebookOut])
def shared_with_me(db: DbSession, user: CurrentUser) -> list[SharedNotebookOut]:
    """Notebooks other people let me see or edit (Ajustes → Cuadernos a los que tengo acceso)."""
    return [
        SharedNotebookOut(
            id=a.notebook.id,
            name=a.notebook.name,
            owner=AuthorOut.model_validate(a.notebook.owner),
            role=a.role,
            granted_at=a.granted_at,
        )
        for a in sharing.shared_with_me(db, user)
    ]


# --- Invitations (owner) ---------------------------------------------------------------------


@router.post("/mine/invitations", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def create_invitation(
    body: InvitationCreate, db: DbSession, user: CurrentUser, lang: Lang
) -> InvitationOut:
    """Get a code to hand to someone. Valid 7 days, one person per code."""
    try:
        invitation = sharing.create_invitation(db, user.notebook, body.role, body.email)
    except sharing.ShareLimitReached:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("share_limit_reached", lang)) from None
    return InvitationOut.model_validate(invitation)


@router.get("/mine/invitations", response_model=list[InvitationOut])
def pending_invitations(db: DbSession, user: CurrentUser) -> list[InvitationOut]:
    return [
        InvitationOut.model_validate(i) for i in sharing.pending_invitations(db, user.notebook.id)
    ]


@router.delete("/mine/invitations/{invitation_id}", response_model=MessageResponse)
def cancel_invitation(
    invitation_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    if not sharing.cancel_invitation(db, user.notebook.id, invitation_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang))
    return MessageResponse(message=t("invitation_cancelled", lang))


# --- Joining (guest) -------------------------------------------------------------------------


@router.post("/join", response_model=SharedNotebookOut)
def join_notebook(body: JoinRequest, db: DbSession, user: CurrentUser, lang: Lang):
    """'Unirme a un cuaderno': type the code you were given."""
    try:
        access = sharing.join(db, user, body.code)
    except sharing.InvalidInvitation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, t("invitation_invalid", lang)) from None
    except sharing.OwnNotebook:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, t("invitation_own_notebook", lang)
        ) from None
    except sharing.ShareLimitReached:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, t("share_limit_reached_owner", lang)
        ) from None
    notebook = access.notebook
    return SharedNotebookOut(
        id=notebook.id,
        name=notebook.name,
        owner=AuthorOut.model_validate(notebook.owner),
        role=access.role,
        granted_at=access.granted_at,
    )


# --- Accesses (owner) ------------------------------------------------------------------------


@router.get("/mine/access", response_model=list[AccessOut])
def my_accesses(db: DbSession, user: CurrentUser) -> list[AccessOut]:
    """People who can see or edit my notebook."""
    return [_access_out(a) for a in sharing.accesses(db, user.notebook.id)]


@router.patch("/mine/access/{user_id}", response_model=AccessOut)
def change_role(
    user_id: int, body: RoleChange, db: DbSession, user: CurrentUser, lang: Lang
) -> AccessOut:
    try:
        access = sharing.change_role(db, user.notebook.id, user_id, body.role)
    except sharing.AccessNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang)) from None
    return _access_out(access)


@router.delete("/mine/access/{user_id}", response_model=MessageResponse)
def remove_access(user_id: int, db: DbSession, user: CurrentUser, lang: Lang) -> MessageResponse:
    try:
        sharing.remove_access(db, user.notebook.id, user_id)
    except sharing.AccessNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("not_found", lang)) from None
    return MessageResponse(message=t("access_removed", lang))


@router.delete("/{notebook_id}/access/me", response_model=MessageResponse)
def leave_notebook(
    notebook_id: int, db: DbSession, user: CurrentUser, lang: Lang
) -> MessageResponse:
    """Leave a notebook someone shared with me."""
    try:
        permissions.get_notebook(db, notebook_id)
        sharing.remove_access(db, notebook_id, user.id)
    except (permissions.NotebookNotFound, sharing.AccessNotFound):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None
    return MessageResponse(message=t("left_notebook", lang))
