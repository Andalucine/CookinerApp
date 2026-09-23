"""Notebooks: every account owns exactly one; other people may be given viewer/editor access."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.user import User

ROLE_VIEWER = "viewer"
ROLE_EDITOR = "editor"
ROLES = (ROLE_VIEWER, ROLE_EDITOR)


class Notebook(TimestampMixin, Base):
    """The personal cookbook of one account. Created automatically on registration."""

    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="notebook", foreign_keys=[owner_id])
    accesses: Mapped[list["NotebookAccess"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="notebook")


class NotebookAccess(Base):
    """Someone other than the owner who can see (viewer) or add/edit (editor) a notebook."""

    __tablename__ = "notebook_access"
    __table_args__ = (UniqueConstraint("notebook_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(10), default=ROLE_VIEWER, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notebook: Mapped[Notebook] = relationship(back_populates="accesses")
    user: Mapped["User"] = relationship(back_populates="notebook_accesses")


class NotebookInvitation(Base):
    """Invitation code to enter someone's notebook with a given role."""

    __tablename__ = "notebook_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invited_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(10), default=ROLE_VIEWER, nullable=False)
    invited_email: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notebook: Mapped[Notebook] = relationship()
