"""Wines (global catalogue) and wine recommendations per recipe."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Wine(TimestampMixin, Base):
    __tablename__ = "wines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    winery: Mapped[str | None] = mapped_column(String(200))
    appellation: Mapped[str | None] = mapped_column(String(100))  # D.O. Ribera del Duero...
    # 'red', 'white', 'rose', 'sparkling', 'fortified', 'other'
    wine_type: Mapped[str | None] = mapped_column(String(20))
    grapes: Mapped[str | None] = mapped_column(String(200))
    vintage: Mapped[int | None] = mapped_column(Integer)
    tasting_notes: Mapped[str | None] = mapped_column(Text)
    pairing_notes: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(1000))


class RecipeWine(Base):
    """Wine recommended for a recipe, with the reason."""

    __tablename__ = "recipe_wines"
    __table_args__ = (UniqueConstraint("recipe_id", "wine_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wine_id: Mapped[int] = mapped_column(
        ForeignKey("wines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(10), default="manual", nullable=False)  # imported
    added_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    wine: Mapped[Wine] = relationship()
