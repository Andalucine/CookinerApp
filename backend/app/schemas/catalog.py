"""Read-only catalogue models: categories, tags, seasons, occasions, sections, ingredients."""

from pydantic import BaseModel, ConfigDict


class Named(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_es: str
    name_en: str


class SeasonOut(Named):
    code: str


class OccasionOut(Named):
    is_preloaded: bool


class ShoppingSectionOut(Named):
    code: str
    position: int


class TagOut(Named):
    kind: str
    code: str


class CategoryOut(Named):
    slug: str
    level: int
    examples_es: str | None = None
    children: list["CategoryOut"] = []


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_en: str | None = None
    is_spice: bool
    shopping_section_id: int | None = None
