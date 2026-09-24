"""The shop's wines (session 9: the Vinoselección catalogue, the same for every notebook), the
wines recommended for a recipe and the automatic pairing suggestion."""

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models import (
    Category,
    Favorite,
    PairingRule,
    Recipe,
    RecipeWine,
    User,
    Wine,
    WineCategory,
)
from app.models.wine import ORIGIN_MANUAL, SHOP_NAMES, SHOP_VINOSELECCION
from app.schemas.catalog import local_text
from app.schemas.wine import WineIn

# How many shop wines the automatic suggestion of a recipe shows
SUGGESTED_WINES = 6


class WineNotFound(Exception):
    pass


class RecipeWineNotFound(Exception):
    pass


def _query():
    return select(Wine).options(selectinload(Wine.category).selectinload(WineCategory.parent))


def get(db: Session, wine_id: int) -> Wine:
    wine = db.scalar(_query().where(Wine.id == wine_id))
    if wine is None:
        raise WineNotFound
    return wine


def shop_url(url: str, params: str | None = None) -> str:
    """The wine's page with the agent's code added (settings.shop_link_params), so that the
    shop knows the sale came from CookinerApp. Without a code, the page as it is."""
    extra = (get_settings().shop_link_params if params is None else params).strip().lstrip("?&")
    if not extra:
        return url
    scheme, netloc, path, query, fragment = urlsplit(url)
    query = f"{query}&{extra}" if query else extra
    return urlunsplit((scheme, netloc, path, query, fragment))


def upsert(db: Session, data: WineIn, shop: str = SHOP_VINOSELECCION) -> tuple[Wine, bool]:
    """Save a wine read from the shop: new, or the one with the same page updated (price, notes,
    stock...). Returns (wine, created). The sync script commits."""
    wine = db.scalar(select(Wine).where(Wine.source_url == data.source_url))
    created = wine is None
    if created:
        wine = Wine(shop=shop, source_url=data.source_url)
        db.add(wine)
    for field, value in data.model_dump().items():
        setattr(wine, field, value)
    wine.source_name = SHOP_NAMES.get(shop, data.source_name)
    wine.in_stock = True
    wine.checked_at = datetime.now(UTC)
    return wine, created


@dataclass
class WineFilters:
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
    in_stock_only: bool = False


def _category_ids(db: Session, category_id: int) -> list[int]:
    children = db.scalars(select(WineCategory.id).where(WineCategory.parent_id == category_id))
    return [category_id, *children]


def search(db: Session, f: WineFilters, limit: int = 50, offset: int = 0) -> tuple[int, list]:
    q = select(Wine.id)
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
    if f.in_stock_only:
        q = q.where(Wine.in_stock.is_(True))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    # What can be bought first; sold-out wines stay findable at the end
    order = (Wine.in_stock.desc(), Wine.name, Wine.id)
    ids = list(db.scalars(q.order_by(*order).limit(limit).offset(offset)))
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
                selectinload(RecipeWine.wine)
                .selectinload(Wine.category)
                .selectinload(WineCategory.parent),
                selectinload(RecipeWine.added_by),
            )
            .where(RecipeWine.recipe_id == recipe.id)
            .order_by(RecipeWine.id)
        )
    )


def add_to_recipe(db: Session, user: User, recipe: Recipe, wine_id: int, reason: str | None):
    """Recommend a wine of the shop for the recipe (or update the reason)."""
    if db.get(Wine, wine_id) is None:
        raise WineNotFound
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


def suggest(db: Session, recipe: Recipe, user_id: int | None = None) -> Suggestion | None:
    """Pairing rules for the recipe's categories (primary first); a subcategory without rules
    uses its parent's. Plus a few shop wines of the suggested types: the person's favourites
    first, then those in stock, in the order of the rules."""
    ordered = sorted(recipe.categories, key=lambda rc: not rc.is_primary)
    for rc in ordered:
        category: Category | None = rc.category
        while category is not None:
            rules = _rules_for(db, category.id)
            if rules:
                wine_type_ids = [r.wine_category_id for r in rules]
                rank = case({cid: i for i, cid in enumerate(wine_type_ids)}, value=Wine.category_id)
                query = _query().where(Wine.category_id.in_(wine_type_ids))
                order = [Wine.in_stock.desc(), rank, Wine.name]
                if user_id:
                    starred = exists().where(
                        Favorite.wine_id == Wine.id, Favorite.user_id == user_id
                    )
                    query = query.where(or_(Wine.in_stock.is_(True), starred))
                    order.insert(0, starred.desc())
                else:
                    query = query.where(Wine.in_stock.is_(True))
                wines = db.scalars(query.order_by(*order).limit(SUGGESTED_WINES)).all()
                return Suggestion(based_on=category, rules=rules, wines=list(wines))
            category = category.parent
    return None


def category_counts(db: Session) -> dict[int, int]:
    """Wines of the shop per type (in stock), each counted in its type and in the parent type."""
    parents = dict(db.execute(select(WineCategory.id, WineCategory.parent_id)).all())
    rows = db.execute(
        select(Wine.category_id).where(Wine.category_id.isnot(None), Wine.in_stock.is_(True))
    ).all()
    counts: dict[int, int] = {}
    for (category_id,) in rows:
        current = category_id
        while current is not None:
            counts[current] = counts.get(current, 0) + 1
            current = parents.get(current)
    return counts


def recipes_of(db: Session, wine: Wine, notebook_id: int) -> list[RecipeWine]:
    """The recipes of a notebook this wine is recommended for (Ficha del vino → 'Recomendado
    para'). The wine is shared by every notebook, so only that notebook's recipes."""
    return list(
        db.scalars(
            select(RecipeWine)
            .join(Recipe, Recipe.id == RecipeWine.recipe_id)
            .options(selectinload(RecipeWine.recipe), selectinload(RecipeWine.added_by))
            .where(RecipeWine.wine_id == wine.id, Recipe.notebook_id == notebook_id)
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
    """A page of the shop read by the importer, as a wine to save (session 8, used by the sync
    since session 9): its type found by slug and, when the page says nothing about pairing,
    "con qué marida" from the pairing rules."""
    category = category_by_slug(db, preview.category_slug)
    paired = categories_paired_with(db, category.id if category else None)
    pairing = preview.pairing_notes or (
        ", ".join(local_text(c, lang) or "" for c in paired) or None
    )
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
