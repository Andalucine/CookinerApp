"""Free notes of a notebook: menus, tricks, suppliers, ideas. Independent from recipes."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.notebook import Notebook
from app.models.user import User

# What a note is about (session 9): the app shows its icon in a yellow square in the list
NOTE_KINDS = ("recipes", "wines", "spices", "celebrations", "shopping", "ideas")


class Note(TimestampMixin, Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Last person who changed it, to show "(editado por NOMBRE)" when it is not the owner
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(String(20))  # one of NOTE_KINDS, or none

    notebook: Mapped[Notebook] = relationship()
    author: Mapped[User | None] = relationship(foreign_keys=[author_id])
    updated_by: Mapped[User | None] = relationship(foreign_keys=[updated_by_id])
