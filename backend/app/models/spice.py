"""Spice zone: general equivalence rules, substitutions and blend compositions.

Spices themselves are rows of `ingredients` with `is_spice = true`. The catalogue is global;
each notebook can add its own blends and its own version of a catalogue blend (session 8).
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.taxonomy import Ingredient

if TYPE_CHECKING:
    from app.models.notebook import Notebook
    from app.models.user import User


class SpiceEquivalenceRule(Base):
    """General rules shown at the top of the spice zone (fresh → dried, whole → ground...)."""

    __tablename__ = "spice_equivalence_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    situation_es: Mapped[str] = mapped_column(String(120), nullable=False)
    situation_en: Mapped[str] = mapped_column(String(120), nullable=False)
    equivalence_es: Mapped[str] = mapped_column(String(200), nullable=False)
    equivalence_en: Mapped[str] = mapped_column(String(200), nullable=False)
    note_es: Mapped[str | None] = mapped_column(String(200))
    note_en: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class SpiceSubstitution(Base):
    """'If you have no X, use Y' with the ratio (per 1 tsp of X) and what changes."""

    __tablename__ = "spice_substitutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The substitute as text ("Canela + nuez moscada, mitad y mitad"); linked to an ingredient
    # when it is a single one, so the pantry can check whether the user has it.
    substitute_es: Mapped[str] = mapped_column(String(150), nullable=False)
    substitute_en: Mapped[str] = mapped_column(String(150), nullable=False)
    substitute_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL")
    )
    ratio: Mapped[str | None] = mapped_column(String(60))  # "1 : ½", "1 cda fresca = 1 cdta seca"
    note_es: Mapped[str | None] = mapped_column(String(200))
    note_en: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ingredient: Mapped[Ingredient] = relationship(foreign_keys=[ingredient_id])
    substitute: Mapped[Ingredient | None] = relationship(foreign_keys=[substitute_id])


class SpiceBlend(Base):
    """Composition of a spice blend (curry, ras el hanout...) to make it at home."""

    __tablename__ = "spice_blends"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    quick_substitute_es: Mapped[str | None] = mapped_column(String(150))
    quick_substitute_en: Mapped[str | None] = mapped_column(String(150))
    note_es: Mapped[str | None] = mapped_column(String(200))
    note_en: Mapped[str | None] = mapped_column(String(200))

    ingredient: Mapped[Ingredient] = relationship()
    items: Mapped[list["SpiceBlendItem"]] = relationship(
        back_populates="blend", cascade="all, delete-orphan", order_by="SpiceBlendItem.position"
    )


class SpiceBlendItem(Base):
    __tablename__ = "spice_blend_items"
    __table_args__ = (UniqueConstraint("blend_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    blend_id: Mapped[int] = mapped_column(
        ForeignKey("spice_blends.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    parts: Mapped[str] = mapped_column(String(10), nullable=False)  # "2", "½", "¼"
    is_optional: Mapped[bool] = mapped_column(default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    blend: Mapped[SpiceBlend] = relationship(back_populates="items")
    ingredient: Mapped[Ingredient] = relationship()


class NotebookBlend(TimestampMixin, Base):
    """A blend of one notebook: a new one ("mezcla de la abuela") or the notebook's own version
    of a catalogue blend (same `ingredient_id` as the catalogue `SpiceBlend`). The catalogue
    row is never changed; deleting the notebook's version goes back to it."""

    __tablename__ = "notebook_blends"
    __table_args__ = (UniqueConstraint("notebook_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The blend's name lives in the global ingredient catalogue, like every ingredient, so that
    # a recipe that uses "mezcla de la abuela" links to the same row.
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    note: Mapped[str | None] = mapped_column(String(200))

    notebook: Mapped["Notebook"] = relationship()
    ingredient: Mapped[Ingredient] = relationship()
    created_by: Mapped["User | None"] = relationship()
    items: Mapped[list["NotebookBlendItem"]] = relationship(
        back_populates="blend", cascade="all, delete-orphan", order_by="NotebookBlendItem.position"
    )


class NotebookBlendItem(Base):
    __tablename__ = "notebook_blend_items"
    __table_args__ = (UniqueConstraint("blend_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    blend_id: Mapped[int] = mapped_column(
        ForeignKey("notebook_blends.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    parts: Mapped[str] = mapped_column(String(10), nullable=False)  # "2", "½", "¼"
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    blend: Mapped[NotebookBlend] = relationship(back_populates="items")
    ingredient: Mapped[Ingredient] = relationship()


class NotebookSpice(TimestampMixin, Base):
    """A spice added by one notebook ("pimentón de mi pueblo"), in one of the seven families.
    The name lives in `ingredients` like every ingredient; the family and the other names are
    the notebook's."""

    __tablename__ = "notebook_spices"
    __table_args__ = (UniqueConstraint("notebook_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family: Mapped[str] = mapped_column(String(30), nullable=False)
    aliases: Mapped[str | None] = mapped_column(String(300))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    ingredient: Mapped[Ingredient] = relationship()
    created_by: Mapped["User | None"] = relationship()


class NotebookSubstitution(Base):
    """The notebook's own list of substitutes for an ingredient (catalogue spice or its own).
    When a notebook has rows for an ingredient, they replace the catalogue's list for it."""

    __tablename__ = "notebook_substitutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    substitute: Mapped[str] = mapped_column(String(150), nullable=False)
    substitute_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL")
    )
    ratio: Mapped[str | None] = mapped_column(String(60))
    note: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    created_by: Mapped["User | None"] = relationship()


class NotebookSpicePairing(Base):
    """The notebook's own "va bien con" for an ingredient (catalogue spice or its own); when it
    exists it replaces the catalogue's text for that notebook."""

    __tablename__ = "notebook_spice_pairings"
    __table_args__ = (UniqueConstraint("notebook_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pairs_with: Mapped[str] = mapped_column(String(300), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    created_by: Mapped["User | None"] = relationship()
