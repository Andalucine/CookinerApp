"""All ORM models. Importing this package registers every table on Base.metadata."""

from app.models.favorite import Favorite
from app.models.import_job import ImportJob
from app.models.note import Note
from app.models.notebook import Notebook, NotebookAccess, NotebookInvitation
from app.models.pantry import PantryItem, ShoppingListItem
from app.models.recipe import (
    Recipe,
    RecipeCategory,
    RecipeContribution,
    RecipeIngredient,
    RecipeOccasion,
    RecipeSeason,
    RecipeTag,
)
from app.models.spice import (
    NotebookBlend,
    NotebookBlendItem,
    NotebookSpice,
    NotebookSubstitution,
    SpiceBlend,
    SpiceBlendItem,
    SpiceEquivalenceRule,
    SpiceSubstitution,
)
from app.models.taxonomy import Category, Ingredient, Occasion, Season, ShoppingSection, Tag
from app.models.user import AuthIdentity, PasswordResetToken, User
from app.models.wine import PairingRule, RecipeWine, Wine, WineCategory

__all__ = [
    "AuthIdentity",
    "Category",
    "Favorite",
    "ImportJob",
    "Ingredient",
    "Note",
    "Notebook",
    "NotebookAccess",
    "NotebookBlend",
    "NotebookBlendItem",
    "NotebookSpice",
    "NotebookSubstitution",
    "NotebookInvitation",
    "Occasion",
    "PairingRule",
    "PantryItem",
    "PasswordResetToken",
    "Recipe",
    "RecipeCategory",
    "RecipeContribution",
    "RecipeIngredient",
    "RecipeOccasion",
    "RecipeSeason",
    "RecipeTag",
    "RecipeWine",
    "Season",
    "ShoppingListItem",
    "ShoppingSection",
    "SpiceBlend",
    "SpiceBlendItem",
    "SpiceEquivalenceRule",
    "SpiceSubstitution",
    "Tag",
    "User",
    "Wine",
    "WineCategory",
]
