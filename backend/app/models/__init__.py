"""All ORM models. Importing this package registers every table on Base.metadata."""

from app.models.group import Group, GroupInvitation, GroupMember
from app.models.import_job import ImportJob
from app.models.recipe import (
    Recipe,
    RecipeContribution,
    RecipeEditor,
    RecipeIngredient,
    RecipeOccasion,
    RecipeSeason,
)
from app.models.taxonomy import Ingredient, Occasion, Season
from app.models.user import AuthIdentity, PasswordResetToken, User
from app.models.wine import RecipeWine, Wine

__all__ = [
    "AuthIdentity",
    "Group",
    "GroupInvitation",
    "GroupMember",
    "ImportJob",
    "Ingredient",
    "Occasion",
    "PasswordResetToken",
    "Recipe",
    "RecipeContribution",
    "RecipeEditor",
    "RecipeIngredient",
    "RecipeOccasion",
    "RecipeSeason",
    "RecipeWine",
    "Season",
    "User",
    "Wine",
]
