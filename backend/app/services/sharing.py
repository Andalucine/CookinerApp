"""Sharing a notebook: invitations by code, joining, roles and access management."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Notebook, NotebookAccess, NotebookInvitation, User
from app.models.notebook import ROLES

# No 0/O or 1/I: the code is typed by hand from a message or read over the phone
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
INVITATION_DAYS = 7


class ShareLimitReached(Exception):
    pass


class InvalidInvitation(Exception):
    """Unknown, expired, already used, or for another email."""


class OwnNotebook(Exception):
    pass


class InvalidRole(Exception):
    pass


class AccessNotFound(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)  # SQLite (tests) returns naive datetimes


def shared_with_count(db: Session, notebook_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(NotebookAccess)
            .where(NotebookAccess.notebook_id == notebook_id)
        )
        or 0
    )


def _check_share_limit(db: Session, notebook: Notebook) -> None:
    limit = notebook.owner.max_shared_with
    if limit is not None and shared_with_count(db, notebook.id) >= limit:
        raise ShareLimitReached


def _generate_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if db.scalar(select(NotebookInvitation).where(NotebookInvitation.code == code)) is None:
            return code


def create_invitation(
    db: Session, notebook: Notebook, role: str, email: str | None
) -> NotebookInvitation:
    if role not in ROLES:
        raise InvalidRole
    _check_share_limit(db, notebook)
    invitation = NotebookInvitation(
        notebook_id=notebook.id,
        invited_by_id=notebook.owner_id,
        code=_generate_code(db),
        role=role,
        invited_email=email.lower().strip() if email else None,
        expires_at=_now() + timedelta(days=INVITATION_DAYS),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def pending_invitations(db: Session, notebook_id: int) -> list[NotebookInvitation]:
    rows = db.scalars(
        select(NotebookInvitation)
        .where(
            NotebookInvitation.notebook_id == notebook_id,
            NotebookInvitation.accepted_at.is_(None),
        )
        .order_by(NotebookInvitation.created_at.desc())
    ).all()
    now = _now()
    return [i for i in rows if _aware(i.expires_at) > now]


def cancel_invitation(db: Session, notebook_id: int, invitation_id: int) -> bool:
    invitation = db.get(NotebookInvitation, invitation_id)
    if invitation is None or invitation.notebook_id != notebook_id or invitation.accepted_at:
        return False
    db.delete(invitation)
    db.commit()
    return True


def join(db: Session, user: User, code: str) -> NotebookAccess:
    """Use an invitation code. Returns the access (new, or updated to the invitation's role)."""
    invitation = db.scalar(
        select(NotebookInvitation)
        .options(selectinload(NotebookInvitation.notebook).selectinload(Notebook.owner))
        .where(NotebookInvitation.code == code.strip().upper())
    )
    if invitation is None or invitation.accepted_at or _aware(invitation.expires_at) < _now():
        raise InvalidInvitation
    if invitation.invited_email and invitation.invited_email != user.email:
        raise InvalidInvitation
    notebook = invitation.notebook
    if notebook.owner_id == user.id:
        raise OwnNotebook

    access = db.scalar(
        select(NotebookAccess).where(
            NotebookAccess.notebook_id == notebook.id, NotebookAccess.user_id == user.id
        )
    )
    if access is None:
        _check_share_limit(db, notebook)
        access = NotebookAccess(notebook_id=notebook.id, user_id=user.id, role=invitation.role)
        db.add(access)
    else:
        access.role = invitation.role  # already inside: the new code changes the role
    invitation.accepted_at = _now()
    invitation.accepted_by_id = user.id
    db.commit()
    db.refresh(access)
    return access


def accesses(db: Session, notebook_id: int) -> list[NotebookAccess]:
    return db.scalars(
        select(NotebookAccess)
        .options(selectinload(NotebookAccess.user))
        .where(NotebookAccess.notebook_id == notebook_id)
        .order_by(NotebookAccess.granted_at)
    ).all()


def _get_access(db: Session, notebook_id: int, user_id: int) -> NotebookAccess:
    access = db.scalar(
        select(NotebookAccess).where(
            NotebookAccess.notebook_id == notebook_id, NotebookAccess.user_id == user_id
        )
    )
    if access is None:
        raise AccessNotFound
    return access


def change_role(db: Session, notebook_id: int, user_id: int, role: str) -> NotebookAccess:
    if role not in ROLES:
        raise InvalidRole
    access = _get_access(db, notebook_id, user_id)
    access.role = role
    db.commit()
    db.refresh(access)
    return access


def remove_access(db: Session, notebook_id: int, user_id: int) -> None:
    access = _get_access(db, notebook_id, user_id)
    db.delete(access)
    db.commit()


def shared_with_me(db: Session, user: User) -> list[NotebookAccess]:
    return db.scalars(
        select(NotebookAccess)
        .options(selectinload(NotebookAccess.notebook).selectinload(Notebook.owner))
        .where(NotebookAccess.user_id == user.id)
        .order_by(NotebookAccess.granted_at)
    ).all()
