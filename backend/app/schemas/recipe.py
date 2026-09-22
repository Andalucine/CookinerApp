"""Recipe input/output models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import Named, OccasionOut, SeasonOut, TagOut

SOURCE_TYPES = ("own", "web", "book", "family", "other")


class RecipeIngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Ingredient name, any case")
    quantity: float | None = None
    unit: str | None = Field(default=None, max_length=30)
    raw_text: str | None = Field(default=None, max_length=200)


class RecipeIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    instructions: str | None = None
    prep_time_minutes: int | None = Field(default=None, ge=0)
    servings: int | None = Field(default=None, ge=1)
    cook_name: str | None = Field(default=None, max_length=100)
    source_type: str = Field(default="own", pattern="^(own|web|book|family|other)$")
    source_name: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=1000)
    youtube_url: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=1000)
    language: str = Field(default="es", pattern="^(es|en)$")
    ingredients: list[RecipeIngredientIn] = []
    category_ids: list[int] = Field(default=[], description="First one is the primary category")
    tag_ids: list[int] = []
    season_ids: list[int] = []
    occasion_ids: list[int] = []


class RecipeCreate(RecipeIn):
    notebook_id: int | None = Field(
        default=None, description="Notebook to add the recipe to; your own if omitted"
    )


class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    name: str
    quantity: float | None = None
    unit: str | None = None
    raw_text: str | None = None
    position: int


class RecipeCategoryOut(Named):
    slug: str
    is_primary: bool


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str


class RecipeSummary(BaseModel):
    """What a list or a search returns: enough for the card."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    notebook_id: int
    title: str
    prep_time_minutes: int | None = None
    time_label: str | None = None  # quick | medium | long
    image_url: str | None = None
    cook_name: str | None = None
    source_type: str
    author: AuthorOut | None = None  # None when the author deleted their account
    added_by: str | None = None  # display name when the author is not the notebook owner
    primary_category: RecipeCategoryOut | None = None
    is_favorite: bool = False


class RecipeOut(RecipeSummary):
    description: str | None = None
    instructions: str | None = None
    servings: int | None = None
    source_name: str | None = None
    source_url: str | None = None
    youtube_url: str | None = None
    language: str
    ingredients: list[RecipeIngredientOut]
    categories: list[RecipeCategoryOut]
    tags: list[TagOut]
    seasons: list[SeasonOut]
    occasions: list[OccasionOut]
    created_at: datetime
    updated_at: datetime


class RecipeSearchResult(BaseModel):
    total: int
    items: list[RecipeSummary]
