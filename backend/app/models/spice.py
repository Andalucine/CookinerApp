"""Spice zone: general equivalence rules, substitutions and blend compositions.

Spices themselves are rows of `ingredients` with `is_spice = true`.
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.taxonomy import Ingredient


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
