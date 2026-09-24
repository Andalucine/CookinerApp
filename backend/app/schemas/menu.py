"""Menú semanal (session 9)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.pantry import ShoppingItemOut
from app.schemas.recipe import RecipeSummary

Meal = Literal["breakfast", "lunch", "dinner"]


class MenuCheckOut(BaseModel):
    """What the notebook can offer before making a draft."""

    week_start: date
    season: str  # spring | summer | autumn | winter
    total_recipes: int
    breakfast_recipes: int  # recipes tagged "desayuno"
    main_recipes: int  # the rest: valid for lunch and dinner


class MenuDraftIn(BaseModel):
    week_start: date  # any day of the week; the API keeps its Monday
    meals: list[Meal] = Field(min_length=1, max_length=3)
    wants: str | None = Field(default=None, max_length=300, description="Foods, comma separated")


class SlotIn(BaseModel):
    recipe_id: int | None = None  # a recipe of the notebook, or none
    note: str | None = Field(default=None, max_length=200)  # written by hand


class SlotOut(BaseModel):
    id: int
    day: int  # 0 = Monday … 6 = Sunday
    meal: Meal
    recipe: RecipeSummary | None = None
    note: str | None = None


class MenuOut(BaseModel):
    id: int
    week_start: date
    meals: list[Meal]
    wants: str | None = None
    slots: list[SlotOut]
    # What the draft could not do as asked (session 9): no_breakfast_recipes,
    # filled_with_rest (not enough recipes with the wanted foods), season_ignored, repeated
    notices: list[str] = []


class MenuShoppingOut(BaseModel):
    added: list[ShoppingItemOut]
    recipes: int  # how many recipes of the week were looked at
