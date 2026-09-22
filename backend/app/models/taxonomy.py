"""Reference tables: ingredients catalogue, seasons and occasions."""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Ingredient(Base):
    """Global catalogue, shared by all groups. `name` is normalised (lowercase, singular)."""

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(50))  # verdura, carne, pescado...


class Season(Base):
    """The four seasons, preloaded."""

    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # spring...
    name_es: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(50), nullable=False)


class Occasion(Base):
    """Occasions/periods: Navidad, Cuaresma... Preloaded ones have group_id NULL."""

    __tablename__ = "occasions"
    __table_args__ = (UniqueConstraint("group_id", "name_es"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    name_es: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(50), nullable=False)
    is_preloaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
