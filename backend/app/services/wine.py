"""Wines of a notebook, the wines recommended for a recipe and the automatic pairing suggestion."""

from dataclasses import dataclass

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Category,
    Favorite,
    Notebook,
    PairingRule,
    Recipe,
    RecipeWine,
    User,
    Wine,
    WineCategory,
)
from app.models.user import PLANS_WITH_WINES
from app.models.wine import ORIGIN_MANUAL
from app.schemas.catalog import local_text
from app.schemas.wine import WineIn


class WineNotFound(Exception):
    pass


class WinesNotInPlan(Exception):
    """The notebook owner's plan has no wine section (free plan)."""


class UnknownWineCategory(Exception):
    pass


class WineInOtherNotebook(Exception):
    pass


class RecipeWineNotFound(Exception):
    pass


def require_wines(notebook: Notebook) -> None:
    """The wine section follows the plan of the notebook OWNER (decision, session 5)."""
    if notebook.owner.plan not in PLANS_WITH_WINES:
        raise WinesNotInPlan


def _query():
    return select(Wine).options(
        selectinload(Wine.category).selectinload(WineCategory.parent),
        selectinload(Wine.notebook).selectinload(Notebook.owner),
        selectinload(Wine.added_by),
        selectinload(Wine.updated_by),
    )


def get(db: Session, wine_id: int) -> Wine:
    wine = db.scalar(_query().where(Wine.id == wine_id))
    if wine is None:
        raise WineNotFound
    return wine


def _apply(db: Session, wine: Wine, data: WineIn) -> None:
    if data.category_id is not None and db.get(WineCategory, data.category_id) is None:
        raise UnknownWineCategory
    for field, value in data.model_dump().items():
        setattr(wine, field, value)


def create(db: Session, user: User, notebook: Notebook, data: WineIn) -> Wine:
    wine = Wine(notebook_id=notebook.id, added_by_id=user.id, updated_by_id=user.id)
    _apply(db, wine, data)
    db.add(wine)
    db.commit()
    return get(db, wine.id)


def update(db: Session, wine: Wine, editor: User, data: WineIn) -> Wine:
    _apply(db, wine, data)
    wine.updated_by_id = editor.id
    db.commit()
    return get(db, wine.id)


def delete(db: Session, wine: Wine) -> None:
    db.delete(wine)
    db.commit()


@dataclass
class WineFilters:
    notebook_ids: list[int]
    text: str | None = None  # name, winery, grapes, appellation
    category_id: int | None = None  # a first-level type includes its children
    sweetness: str | None = None
    body: str | None = None
    ageing: str | None = None
    country: str | None = None
    appellation: str | None = None
    grape: str | None = None
    price_range: str | None = None
    favorites_of: int | None = None


def _category_ids(db: Session, category_id: int) -> list[int]:
    children = db.scalars(select(WineCategory.id).where(WineCategory.parent_id == category_id))
    return [category_id, *children]


def search(db: Session, f: WineFilters, limit: int = 50, offset: int = 0) -> tuple[int, list]:
    q = select(Wine.id).where(Wine.notebook_id.in_(f.notebook_ids))
    if f.text:
        term = f"%{f.text.strip()}%"
        q = q.where(
            or_(
                Wine.name.ilike(term),
                Wine.winery.ilike(term),
                Wine.grapes.ilike(term),
                Wine.appellation.ilike(term),
            )
        )
    if f.category_id:
        q = q.where(Wine.category_id.in_(_category_ids(db, f.category_id)))
    for column, value in (
        (Wine.sweetness, f.sweetness), (Wine.body, f.body), (Wine.ageing, f.ageing),
        (Wine.price_range, f.price_range),
    ):  # fmt: skip
        if value:
            q = q.where(column == value)
    for column, value in (
        (Wine.country, f.country), (Wine.appellation, f.appellation), (Wine.grapes, f.grape),
    ):  # fmt: skip
        if value:
            q = q.where(column.ilike(f"%{value.strip()}%"))
    if f.favorites_of:
        q = q.where(exists().where(Favorite.wine_id == Wine.id, Favorite.user_id == f.favorites_of))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    ids = list(db.scalars(q.order_by(Wine.name, Wine.id).limit(limit).offset(offset)))
    if not ids:
        return total, []
    by_id = {w.id: w for w in db.scalars(_query().where(Wine.id.in_(ids)))}
    return total, [by_id[i] for i in ids]


def favorite_ids(db: Session, user_id: int, wine_ids: list[int]) -> set[int]:
    if not wine_ids:
        return set()
    return set(
        db.scalars(
            select(Favorite.wine_id).where(
                Favorite.user_id == user_id, Favorite.wine_id.in_(wine_ids)
            )
        )
    )


def set_favorite(db: Session, user: User, wine: Wine, on: bool) -> None:
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.wine_id == wine.id)
    )
    if on and existing is None:
        db.add(Favorite(user_id=user.id, wine_id=wine.id))
    elif not on and existing is not None:
        db.delete(existing)
    db.commit()


# --- Wines of a recipe ---------------------------------------------------------------------


def recipe_wines(db: Session, recipe: Recipe) -> list[RecipeWine]:
    return list(
        db.scalars(
            select(RecipeWine)
            .options(
                selectinload(RecipeWine.wine).options(
                    selectinload(Wine.category).selectinload(WineCategory.parent),
                    selectinload(Wine.notebook).selectinload(Notebook.owner),
                    selectinload(Wine.added_by),
                ),
                selectinload(RecipeWine.added_by),
            )
            .where(RecipeWine.recipe_id == recipe.id)
            .order_by(RecipeWine.id)
        )
    )


def add_to_recipe(db: Session, user: User, recipe: Recipe, wine_id: int, reason: str | None):
    """Recommend a wine of the same notebook for the recipe (or update the reason)."""
    wine = db.get(Wine, wine_id)
    if wine is None or wine.notebook_id != recipe.notebook_id:
        raise WineInOtherNotebook
    link = db.scalar(
        select(RecipeWine).where(RecipeWine.recipe_id == recipe.id, RecipeWine.wine_id == wine_id)
    )
    if link is None:
        link = RecipeWine(
            recipe_id=recipe.id, wine_id=wine_id, origin=ORIGIN_MANUAL, added_by_id=user.id
        )
        db.add(link)
    link.reason = reason
    db.commit()
    return link.id


def get_recipe_wine(db: Session, recipe: Recipe, link_id: int) -> RecipeWine:
    link = db.get(RecipeWine, link_id)
    if link is None or link.recipe_id != recipe.id:
        raise RecipeWineNotFound
    return link


def remove_from_recipe(db: Session, link: RecipeWine) -> None:
    db.delete(link)
    db.commit()


@dataclass
class Suggestion:
    based_on: Category
    rules: list[PairingRule]
    wines: list[Wine]


def _rules_for(db: Session, category_id: int) -> list[PairingRule]:
    return list(
        db.scalars(
            select(PairingRule)
            .options(selectinload(PairingRule.wine_category).selectinload(WineCategory.parent))
            .where(PairingRule.recipe_category_id == category_id)
            .order_by(PairingRule.position)
        )
    )


def suggest(db: Session, recipe: Recipe) -> Suggestion | None:
    """Pairing rules for the recipe's categories (primary first); a subcategory without rules
    uses its parent's. Plus the notebook's wines of the suggested types."""
    ordered = sorted(recipe.categories, key=lambda rc: not rc.is_primary)
    for rc in ordered:
        category: Category | None = rc.category
        while category is not None:
            rules = _rules_for(db, category.id)
            if rules:
                wine_type_ids = [r.wine_category_id for r in rules]
                rank = {cid: i for i, cid in enumerate(wine_type_ids)}
                wines = db.scalars(
                    _query().where(
                        Wine.notebook_id == recipe.notebook_id,
                        Wine.category_id.in_(wine_type_ids),
                    )
                ).all()
                wines = sorted(wines, key=lambda w: (rank[w.category_id], w.name))
                return Suggestion(based_on=category, rules=rules, wines=wines)
            category = category.parent
    return None


def category_counts(db: Session, notebook_id: int) -> dict[int, int]:
    """Wines of the notebook per type, each wine counted in its type and in the parent type."""
    parents = dict(db.execute(select(WineCategory.id, WineCategory.parent_id)).all())
    rows = db.execute(
        select(Wine.category_id).where(
            Wine.notebook_id == notebook_id, Wine.category_id.isnot(None)
        )
    ).all()
    counts: dict[int, int] = {}
    for (category_id,) in rows:
        current = category_id
        while current is not None:
            counts[current] = counts.get(current, 0) + 1
            current = parents.get(current)
    return counts


def recipes_of(db: Session, wine: Wine) -> list[RecipeWine]:
    """The recipes this wine is recommended for (Ficha del vino → 'Marida con')."""
    return list(
        db.scalars(
            select(RecipeWine)
            .options(selectinload(RecipeWine.recipe))
            .where(RecipeWine.wine_id == wine.id)
            .order_by(RecipeWine.id)
        )
    )


def category_by_slug(db: Session, slug: str | None) -> WineCategory | None:
    if not slug:
        return None
    return db.scalar(select(WineCategory).where(WineCategory.slug == slug))


def categories_paired_with(db: Session, wine_category_id: int | None) -> list[Category]:
    """Recipe categories whose pairing rules name this wine type (Ficha del vino → Marida con)."""
    if wine_category_id is None:
        return []
    return list(
        db.scalars(
            select(Category)
            .join(PairingRule, PairingRule.recipe_category_id == Category.id)
            .where(PairingRule.wine_category_id == wine_category_id)
            .order_by(PairingRule.position, Category.name_es)
        )
    )


def from_preview(db: Session, preview, url: str, lang: str = "es") -> WineIn:
    """What the app puts in the form after reading a page (session 8): the preview as a wine,
    with its type found by slug and "con qué marida" prefilled from the pairing rules."""
    category = category_by_slug(db, preview.category_slug)
    paired = categories_paired_with(db, category.id if category else None)
    pairing = ", ".join(local_text(c, lang) or "" for c in paired) or None
    return WineIn(
        name=preview.name or "?",  # the form asks for a real name before saving
        winery=preview.winery,
        category_id=category.id if category else None,
        sweetness=preview.sweetness,
        ageing=preview.ageing,
        country=preview.country,
        appellation=preview.appellation,
        grapes=preview.grapes,
        vintage=preview.vintage,
        price_range=preview.price_range,
        tasting_notes=preview.tasting_notes,
        pairing_notes=pairing,
        source_url=url,
        source_name=preview.source_name,
        source_price=preview.source_price,
        image_url=preview.image_url,
    )
