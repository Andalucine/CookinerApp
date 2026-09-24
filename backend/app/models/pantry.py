"""What the notebook has at home (pantry) and what it needs to buy (shopping list)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.taxonomy import Ingredient, ShoppingSection

LOCATION_FRIDGE = "fridge"
LOCATION_FREEZER = "freezer"
LOCATION_PANTRY = "pantry"
LOCATIONS = (LOCATION_FRIDGE, LOCATION_FREEZER, LOCATION_PANTRY)


class PantryItem(Base):
    """An ingredient the notebook currently has. No expiry dates (decision, session 3)."""

    __tablename__ = "pantry_items"
    __table_args__ = (UniqueConstraint("notebook_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[str | None] = mapped_column(String(10))  # fridge | freezer | pantry
    image_url: Mapped[str | None] = mapped_column(String(1000))  # a photo of it (session 9)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ingredient: Mapped[Ingredient] = relationship()


class ShoppingListItem(Base):
    """One line of the notebook's shopping list, placed in its supermarket section."""

    __tablename__ = "shopping_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Linked to the catalogue when it comes from a recipe or the pantry; free text otherwise.
    ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id", ondelete="SET NULL")
    )
    text: Mapped[str] = mapped_column(String(200), nullable=False)  # "pimentón", "2 kg patatas"
    quantity: Mapped[str | None] = mapped_column(String(50))
    section_id: Mapped[int | None] = mapped_column(ForeignKey("shopping_sections.id"))
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"))
    added_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # A photo of the product, to buy just that brand or size (session 9)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ingredient: Mapped[Ingredient | None] = relationship()
    section: Mapped[ShoppingSection | None] = relationship()


class NotebookIngredientSection(Base):
    """The section a notebook chose for an ingredient in its shopping list (session 9): what
    fell in "Otros", or was in the wrong aisle, goes where this notebook buys it from then on.
    The global catalogue is never changed."""

    __tablename__ = "notebook_ingredient_sections"
    __table_args__ = (UniqueConstraint("notebook_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[int] = mapped_column(ForeignKey("shopping_sections.id"), nullable=False)
