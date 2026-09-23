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


def resolve_notebook(db: Session, user: User, notebook_id: int | None, *, edit: bool) -> Notebook:
    """The notebook a request is about (the user's own when omitted), checking the role.

    Raises NotebookNotFound or Forbidden; the API answers 404 in both cases so that nobody
    learns whether a notebook exists.
    """
    if not notebook_id or notebook_id == user.notebook.id:
        return user.notebook
    notebook = get_notebook(db, notebook_id)
    if edit:
        require_edit(db, user, notebook)
    else:
        require_view(db, user, notebook)
    return notebook


def can_delete(user: User, notebook: Notebook, creator_id: int | None) -> bool:
    """Only the notebook owner or whoever created the item can delete it."""
    return user.id in (notebook.owner_id, creator_id)


def added_by(notebook: Notebook, person: User | None) -> str | None:
    """Display name for "(añadido por NOMBRE)": only when it is not the notebook owner."""
    if person is None or person.id == notebook.owner_id:
        return None
    return person.display_name
