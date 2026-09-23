"""Business logic for recipes: create, edit, search, and how they are shown."""

from dataclasses import dataclass

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Category,
    Favorite,
    Ingredient,
    Occasion,
    Recipe,
    RecipeCategory,
    RecipeContribution,
    RecipeIngredient,
    RecipeOccasion,
    RecipeSeason,
    RecipeTag,
    Season,
    ShoppingSection,
    Tag,
    User,
)
from app.schemas.recipe import RecipeIn

QUICK_MAX_MINUTES = 30
MEDIUM_MAX_MINUTES = 60


class RecipeNotFound(Exception):
    pass


class RecipeLimitReached(Exception):
    pass


class UnknownReference(Exception):
    """A category, tag, season or occasion id that does not exist (or an occasion of another
    notebook)."""


def time_label(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    if minutes <= QUICK_MAX_MINUTES:
        return "quick"
    if minutes <= MEDIUM_MAX_MINUTES:
        return "medium"
    return "long"


def normalise_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def get_or_create_ingredient(db: Session, name: str) -> Ingredient:
    """Find an ingredient by name or alias; create it in the global catalogue if new."""
    norm = normalise_name(name)
    ingredient = db.scalar(select(Ingredient).where(Ingredient.name == norm))
    if ingredient is None:
        ingredient = db.scalar(
            select(Ingredient).where(
                or_(
                    Ingredient.aliases == norm,
                    Ingredient.aliases.ilike(f"{norm},%"),
                    Ingredient.aliases.ilike(f"%, {norm}"),
                    Ingredient.aliases.ilike(f"%, {norm},%"),
                )
            )
        )
    if ingredient is None:
        other = db.scalar(select(ShoppingSection).where(ShoppingSection.code == "other"))
        ingredient = Ingredient(name=norm, shopping_section_id=other.id if other else None)
        db.add(ingredient)
        db.flush()
    return ingredient


def _check_ids(db: Session, model, ids: list[int]) -> list:
    if not ids:
        return []
    rows = db.scalars(select(model).where(model.id.in_(ids))).all()
    if len(rows) != len(set(ids)):
        raise UnknownReference
    by_id = {r.id: r for r in rows}
    return [by_id[i] for i in dict.fromkeys(ids)]  # keep the given order, drop duplicates


def _apply(db: Session, recipe: Recipe, data: RecipeIn) -> None:
    """Copy every field of `data` into `recipe`, replacing ingredients and links."""
    for field in (
        "title", "description", "instructions", "prep_time_minutes", "servings", "cook_name",
        "source_type", "source_name", "source_url", "youtube_url", "image_url", "language",
    ):  # fmt: skip
        setattr(recipe, field, getattr(data, field))
    if data.source_type == "web" and not data.source_url:
        raise UnknownReference  # imported/web recipes must keep their source link

    categories = _check_ids(db, Category, data.category_ids)
    tags = _check_ids(db, Tag, data.tag_ids)
    seasons = _check_ids(db, Season, data.season_ids)
    occasions = _check_ids(db, Occasion, data.occasion_ids)
    if any(o.notebook_id not in (None, recipe.notebook_id) for o in occasions):
        raise UnknownReference  # own occasions only work inside their notebook

    if recipe.id is not None:
        # Delete the old rows first so the unique (recipe, category) pairs never collide
        recipe.ingredients.clear()
        recipe.categories.clear()
        db.flush()
    recipe.ingredients = [
        RecipeIngredient(
            ingredient=get_or_create_ingredient(db, item.name),
            quantity=item.quantity,
            unit=item.unit,
            raw_text=item.raw_text,
            position=pos,
        )
        for pos, item in enumerate(data.ingredients)
    ]
    recipe.categories = [
        RecipeCategory(category=c, is_primary=(i == 0)) for i, c in enumerate(categories)
    ]
    recipe.tags = tags
    recipe.seasons = seasons
    recipe.occasions = occasions


def count_in_notebook(db: Session, notebook_id: int) -> int:
    return db.scalar(select(func.count()).where(Recipe.notebook_id == notebook_id)) or 0


def create(db: Session, author: User, notebook_id: int, owner: User, data: RecipeIn) -> Recipe:
    if owner.max_recipes is not None and count_in_notebook(db, notebook_id) >= owner.max_recipes:
        raise RecipeLimitReached
    recipe = Recipe(notebook_id=notebook_id, author_id=author.id)
    _apply(db, recipe, data)
    db.add(recipe)
    db.commit()
    return get(db, recipe.id)


def update(db: Session, recipe: Recipe, editor: User, data: RecipeIn) -> Recipe:
    changed = [
        f
        for f in ("title", "instructions", "ingredients", "description")
        if _new_value(data, f) != _current_value(recipe, f)
    ]
    _apply(db, recipe, data)
    if editor.id != recipe.notebook.owner_id:
        for field in changed:
            db.add(
                RecipeContribution(
                    recipe_id=recipe.id,
                    user_id=editor.id,
                    field=field,
                    content=str(_new_value(data, field))[:2000],
                )
            )
    db.commit()
    return get(db, recipe.id)


def _ingredient_row(name: str, quantity, unit, raw_text) -> dict:
    return {
        "name": normalise_name(name),
        "quantity": float(quantity) if quantity is not None else None,
        "unit": unit,
        "raw_text": raw_text,
    }


def _new_value(data: RecipeIn, field: str):
    if field == "ingredients":
        return [_ingredient_row(i.name, i.quantity, i.unit, i.raw_text) for i in data.ingredients]
    return getattr(data, field)


def _current_value(recipe: Recipe, field: str):
    if field == "ingredients":
        return [
            _ingredient_row(ri.ingredient.name, ri.quantity, ri.unit, ri.raw_text)
            for ri in recipe.ingredients
        ]
    return getattr(recipe, field)


def delete(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
    db.commit()


def _base_query() -> Select:
    return select(Recipe).options(
        selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
        selectinload(Recipe.categories).selectinload(RecipeCategory.category),
        selectinload(Recipe.tags),
        selectinload(Recipe.seasons),
        selectinload(Recipe.occasions),
        selectinload(Recipe.author),
        selectinload(Recipe.notebook),
    )


def get(db: Session, recipe_id: int) -> Recipe:
    recipe = db.scalar(_base_query().where(Recipe.id == recipe_id))
    if recipe is None:
        raise RecipeNotFound
    return recipe


@dataclass
class SearchFilters:
    notebook_ids: list[int]
    text: str | None = None
    ingredients: list[str] | None = None  # every one must be present
    max_minutes: int | None = None
    time: str | None = None  # quick | medium | long
    cook: str | None = None  # cook_name or author display name, partial
    source_type: str | None = None
    source: str | None = None  # source_name partial
    season_id: int | None = None
    occasion_id: int | None = None
    category_id: int | None = None  # includes its subcategories
    tag_ids: list[int] | None = None  # every one must be present
    favorites_of: int | None = None  # user id: only their starred recipes


def category_with_descendants(db: Session, category_id: int) -> list[int]:
    ids = [category_id]
    frontier = [category_id]
    while frontier:
        frontier = list(db.scalars(select(Category.id).where(Category.parent_id.in_(frontier))))
        ids += frontier
    return ids


def category_counts(db: Session, notebook_id: int) -> dict[int, int]:
    """Recipes of the notebook per category, each recipe counted once in every category it
    belongs to and in all their parent categories (Salado ▸ Pescados ▸ Guisos de pescado)."""
    parents = dict(db.execute(select(Category.id, Category.parent_id)).all())
    links = db.execute(
        select(RecipeCategory.recipe_id, RecipeCategory.category_id)
        .join(Recipe, Recipe.id == RecipeCategory.recipe_id)
        .where(Recipe.notebook_id == notebook_id)
    ).all()
    recipes_in: dict[int, set[int]] = {}
    for recipe_id, category_id in links:
        current = category_id
        while current is not None:
            recipes_in.setdefault(current, set()).add(recipe_id)
            current = parents.get(current)
    return {category_id: len(ids) for category_id, ids in recipes_in.items()}


def search(db: Session, f: SearchFilters, limit: int = 50, offset: int = 0) -> tuple[int, list]:
    q = select(Recipe.id).where(Recipe.notebook_id.in_(f.notebook_ids))
    if f.text:
        term = f"%{f.text.strip()}%"
        q = q.where(or_(Recipe.title.ilike(term), Recipe.description.ilike(term)))
    for name in f.ingredients or []:
        term = f"%{normalise_name(name)}%"
        q = q.where(
            exists().where(
                RecipeIngredient.recipe_id == Recipe.id,
                RecipeIngredient.ingredient_id == Ingredient.id,
                or_(Ingredient.name.ilike(term), Ingredient.aliases.ilike(term)),
            )
        )
    if f.max_minutes is not None:
        q = q.where(Recipe.prep_time_minutes <= f.max_minutes)
    if f.time == "quick":
        q = q.where(Recipe.prep_time_minutes <= QUICK_MAX_MINUTES)
    elif f.time == "medium":
        q = q.where(Recipe.prep_time_minutes.between(QUICK_MAX_MINUTES + 1, MEDIUM_MAX_MINUTES))
    elif f.time == "long":
        q = q.where(Recipe.prep_time_minutes > MEDIUM_MAX_MINUTES)
    if f.cook:
        term = f"%{f.cook.strip()}%"
        q = q.join(User, User.id == Recipe.author_id).where(
            or_(Recipe.cook_name.ilike(term), User.display_name.ilike(term))
        )
    if f.source_type:
        q = q.where(Recipe.source_type == f.source_type)
    if f.source:
        term = f"%{f.source.strip()}%"
        q = q.where(or_(Recipe.source_name.ilike(term), Recipe.source_url.ilike(term)))
    if f.season_id:
        q = q.where(
            exists().where(
                RecipeSeason.recipe_id == Recipe.id, RecipeSeason.season_id == f.season_id
            )
        )
    if f.occasion_id:
        q = q.where(
            exists().where(
                RecipeOccasion.recipe_id == Recipe.id, RecipeOccasion.occasion_id == f.occasion_id
            )
        )
    if f.category_id:
        ids = category_with_descendants(db, f.category_id)
        q = q.where(
            exists().where(
                RecipeCategory.recipe_id == Recipe.id, RecipeCategory.category_id.in_(ids)
            )
        )
    for tag_id in f.tag_ids or []:
        q = q.where(exists().where(RecipeTag.recipe_id == Recipe.id, RecipeTag.tag_id == tag_id))
    if f.favorites_of:
        q = q.where(
            exists().where(Favorite.recipe_id == Recipe.id, Favorite.user_id == f.favorites_of)
        )

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    ids = list(
        db.scalars(
            q.order_by(Recipe.updated_at.desc(), Recipe.id.desc()).limit(limit).offset(offset)
        )
    )
    if not ids:
        return total, []
    rows = db.scalars(_base_query().where(Recipe.id.in_(ids))).all()
    by_id = {r.id: r for r in rows}
    return total, [by_id[i] for i in ids]


def favorite_ids(db: Session, user_id: int, recipe_ids: list[int]) -> set[int]:
    if not recipe_ids:
        return set()
    return set(
        db.scalars(
            select(Favorite.recipe_id).where(
                Favorite.user_id == user_id, Favorite.recipe_id.in_(recipe_ids)
            )
        )
    )
