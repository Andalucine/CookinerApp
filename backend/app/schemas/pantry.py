"""Pantry and shopping list models."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeSummary


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str | None = Field(default=None, pattern="^(fridge|freezer|pantry)$")


class PantryItemPhoto(BaseModel):
    image_url: str | None = Field(default=None, max_length=1000)  # None removes the photo


class PantryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    name: str
    location: str | None = None
    image_url: str | None = None


class PantryOut(BaseModel):
    items: list[PantryItemOut]


class MissingIngredient(BaseModel):
    ingredient_id: int
    name: str


class CookableRecipe(BaseModel):
    recipe: RecipeSummary
    missing: list[MissingIngredient]


class WhatCanICookOut(BaseModel):
    complete: list[CookableRecipe]  # everything at home
    missing_one: list[CookableRecipe]  # one ingredient short ("te falta: pimentón")


class ShoppingItemIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    quantity: str | None = Field(default=None, max_length=50)
    ingredient_name: str | None = Field(
        default=None, max_length=100, description="Link to the catalogue to get the section"
    )


class ShoppingItemPatch(BaseModel):
    """Move the line to another section and/or set its photo (session 9). A field that is
    not sent does not change; `image_url: null` removes the photo."""

    section_code: str | None = Field(default=None, min_length=1, max_length=20)
    image_url: str | None = Field(default=None, max_length=1000)


class ShoppingItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    quantity: str | None = None
    ingredient_id: int | None = None
    is_checked: bool
    recipe_id: int | None = None
    image_url: str | None = None


class ShoppingSectionGroup(BaseModel):
    section_id: int | None
    code: str
    name_es: str
    name_en: str
    items: list[ShoppingItemOut]


class ShoppingListOut(BaseModel):
    sections: list[ShoppingSectionGroup]
    total: int
    pending: int
