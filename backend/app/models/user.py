"""Users, their plan, external identities (Google/Apple) and password reset codes."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.notebook import Notebook, NotebookAccess

PLAN_FREE = "free"
PLAN_INDIVIDUAL = "individual"
PLAN_FAMILY = "family"

# Limits per plan (None = unlimited). Copied into the user row on registration so that an
# individual account can be given an exception without changing the plan.
PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    PLAN_FREE: {"max_recipes": 15, "max_shared_with": 0},
    PLAN_INDIVIDUAL: {"max_recipes": None, "max_shared_with": 2},
    PLAN_FAMILY: {"max_recipes": None, "max_shared_with": None},
}
FAMILY_PLAN_ACCOUNTS = 5
# Importing from the web belongs to the paid plans and follows the plan of the notebook owner
# (decision, session 5). The wine section was paid too until session 9: now it is the
# Vinoselección cellar, open to every plan.
PLANS_WITH_IMPORT = frozenset({PLAN_INDIVIDUAL, PLAN_FAMILY})


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Null when the user only signs in with an external identity (Google, Apple...)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(2), default="es", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Plan: 'free' | 'individual' | 'family'. Billing is not implemented yet.
    plan: Mapped[str] = mapped_column(String(20), default=PLAN_FREE, nullable=False)
    max_recipes: Mapped[int | None] = mapped_column(Integer)  # None = unlimited
    max_shared_with: Mapped[int | None] = mapped_column(Integer)  # None = unlimited
    # Family plan: the account that pays; the other (up to 4) accounts point to it.
    family_owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    identities: Mapped[list["AuthIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notebook: Mapped["Notebook"] = relationship(
        back_populates="owner", uselist=False, foreign_keys="Notebook.owner_id"
    )
    notebook_accesses: Mapped[list["NotebookAccess"]] = relationship(back_populates="user")

    @property
    def notebook_id(self) -> int:
        return self.notebook.id


class AuthIdentity(TimestampMixin, Base):
    """External login: provider ('google', 'apple') + the id that provider gives the user."""

    __tablename__ = "auth_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship(back_populates="identities")


class PasswordResetToken(Base):
    """One-time code sent by email for 'forgot my password'."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
