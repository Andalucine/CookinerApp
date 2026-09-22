"""Who can do what on a notebook: owner > editor > viewer > nobody."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Notebook, NotebookAccess, User
from app.models.notebook import ROLE_EDITOR, ROLE_VIEWER

ROLE_OWNER = "owner"


class NotebookNotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def get_notebook(db: Session, notebook_id: int) -> Notebook:
    notebook = db.get(Notebook, notebook_id)
    if notebook is None:
        raise NotebookNotFound
    return notebook


def role_for(db: Session, user: User, notebook: Notebook) -> str | None:
    """'owner', 'editor', 'viewer' or None when the user has no access at all."""
    if notebook.owner_id == user.id:
        return ROLE_OWNER
    access = db.scalar(
        select(NotebookAccess).where(
            NotebookAccess.notebook_id == notebook.id, NotebookAccess.user_id == user.id
        )
    )
    return access.role if access else None


def require_view(db: Session, user: User, notebook: Notebook) -> str:
    role = role_for(db, user, notebook)
    if role not in (ROLE_OWNER, ROLE_EDITOR, ROLE_VIEWER):
        raise Forbidden
    return role


def require_edit(db: Session, user: User, notebook: Notebook) -> str:
    role = role_for(db, user, notebook)
    if role not in (ROLE_OWNER, ROLE_EDITOR):
        raise Forbidden
    return role


def require_owner(user: User, notebook: Notebook) -> None:
    if notebook.owner_id != user.id:
        raise Forbidden


def accessible_notebook_ids(db: Session, user: User) -> list[int]:
    """The user's own notebook plus every notebook shared with them."""
    ids = [user.notebook.id]
    ids += list(
        db.scalars(select(NotebookAccess.notebook_id).where(NotebookAccess.user_id == user.id))
    )
    return ids
