"""Reference tables shared by all notebooks: ingredients, seasons, occasions, categories,
tags and shopping sections."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ShoppingSection(Base):
    """Supermarket sections, in the order you walk through the shop."""

    __tablename__ = "shopping_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)  # produce, meat...
    name_es: Mapped[str] = mapped_column(String(60), nullable=False)
    name_en: Mapped[str] = mapped_column(String(60), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(60))
    name_nl: Mapped[str | None] = mapped_column(String(60))
    name_de: Mapped[str | None] = mapped_column(String(60))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Ingredient(Base):
    """Global catalogue. `name` is normalised (lowercase, singular). Spices are ingredients too."""

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    name_fr: Mapped[str | None] = mapped_column(String(100))
    name_nl: Mapped[str | None] = mapped_column(String(100))
    name_de: Mapped[str | None] = mapped_column(String(100))
    # Other names people use ("hierbabuena", "matalahúva"), comma separated
    aliases: Mapped[str | None] = mapped_column(String(300))
    is_spice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # 'herbs', 'seeds', 'barks_roots_flowers', 'peppers_chillies', 'paprikas', 'blends',
    # 'salts_seasonings' — only for spices
    spice_family: Mapped[str | None] = mapped_column(String(30))
    # "Va bien con": the foods the spice is recommended with (session 8), only for spices
    pairs_with_es: Mapped[str | None] = mapped_column(String(200))
    pairs_with_en: Mapped[str | None] = mapped_column(String(200))
    pairs_with_fr: Mapped[str | None] = mapped_column(String(200))
    pairs_with_nl: Mapped[str | None] = mapped_column(String(200))
    pairs_with_de: Mapped[str | None] = mapped_column(String(200))
    shopping_section_id: Mapped[int | None] = mapped_column(ForeignKey("shopping_sections.id"))

    shopping_section: Mapped[ShoppingSection | None] = relationship()


class Season(Base):
    """The four seasons, preloaded."""

    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # spring...
    name_es: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(50), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(50))
    name_nl: Mapped[str | None] = mapped_column(String(50))
    name_de: Mapped[str | None] = mapped_column(String(50))


class Occasion(Base):
    """Occasions/periods: Navidad, Cuaresma... Preloaded ones have notebook_id NULL.

    A notebook can add its own (session 5): the name the user writes goes into both name_es and
    name_en, since it is not translated.
    """

    __tablename__ = "occasions"
    __table_args__ = (UniqueConstraint("notebook_id", "name_es"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int | None] = mapped_column(ForeignKey("notebooks.id", ondelete="CASCADE"))
    name_es: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(50), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(50))
    name_nl: Mapped[str | None] = mapped_column(String(50))
    name_de: Mapped[str | None] = mapped_column(String(50))
    is_preloaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    created_by: Mapped["User | None"] = relationship()


class Category(Base):
    """Recipe category tree, three levels: branch (Salado/Dulce/Bebidas) → category → subcategory.

    Global and closed in v1 (`notebook_id` NULL). The column is there so that a notebook can add
    its own subcategories later, as occasions already allow.
    """

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("parent_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    notebook_id: Mapped[int | None] = mapped_column(ForeignKey("notebooks.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(60), nullable=False)
    name_es: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(80))
    name_nl: Mapped[str | None] = mapped_column(String(80))
    name_de: Mapped[str | None] = mapped_column(String(80))
    examples_es: Mapped[str | None] = mapped_column(String(200))  # "gazpacho, salmorejo"
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 branch, 2 category, 3 sub
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_preloaded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped["Category | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", order_by="Category.position"
    )


class Tag(Base):
    """Closed lists the user ticks.

    kind = 'course' | 'method' | 'diet' | 'difficulty' | 'origin'.
    """

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("kind", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name_es: Mapped[str] = mapped_column(String(60), nullable=False)
    name_en: Mapped[str] = mapped_column(String(60), nullable=False)
    name_fr: Mapped[str | None] = mapped_column(String(60))
    name_nl: Mapped[str | None] = mapped_column(String(60))
    name_de: Mapped[str | None] = mapped_column(String(60))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
