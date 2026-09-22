"""Recipes and everything attached to them."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.taxonomy import Ingredient, Occasion, Season
    from app.models.user import User


class Recipe(TimestampMixin, Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer)
    servings: Mapped[int | None] = mapped_column(Integer)
    # Free-text cook for people who don't use the app ("la abuela Carmen")
    cook_name: Mapped[str | None] = mapped_column(String(100))
    # 'own', 'web', 'book', 'family', 'other'
    source_type: Mapped[str] = mapped_column(String(20), default="own", nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    youtube_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    language: Mapped[str] = mapped_column(String(2), default="es", nullable=False)

    group: Mapped["Group"] = relationship(back_populates="recipes")
    author: Mapped["User"] = relationship()
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeIngredient.position"
    )
    seasons: Mapped[list["Season"]] = relationship(secondary="recipe_seasons")
    occasions: Mapped[list["Occasion"]] = relationship(secondary="recipe_occasions")
    editors: Mapped[list["RecipeEditor"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    contributions: Mapped[list["RecipeContribution"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"), nullable=False, index=True
    )
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 2))
    unit: Mapped[str | None] = mapped_column(String(30))  # g, ml, unidad, cucharada...
    raw_text: Mapped[str | None] = mapped_column(String(200))  # "2 tomates maduros"
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship()


class RecipeSeason(Base):
    __tablename__ = "recipe_seasons"
    __table_args__ = (UniqueConstraint("recipe_id", "season_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)


class RecipeOccasion(Base):
    __tablename__ = "recipe_occasions"
    __table_args__ = (UniqueConstraint("recipe_id", "occasion_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    occasion_id: Mapped[int] = mapped_column(
        ForeignKey("occasions.id", ondelete="CASCADE"), nullable=False
    )


class RecipeEditor(Base):
    """Users the author has authorised to edit this recipe."""

    __tablename__ = "recipe_editors"
    __table_args__ = (UniqueConstraint("recipe_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recipe: Mapped[Recipe] = relationship(back_populates="editors")


class RecipeContribution(Base):
    """Something added to someone else's recipe, shown as '(añadido por NOMBRE)'."""

    __tablename__ = "recipe_contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # instructions, ingredients...
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recipe: Mapped[Recipe] = relationship(back_populates="contributions")
    user: Mapped["User"] = relationship()
