"""Global catalogues the app needs to show pickers: read-only, no login required."""

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import DbSession
from app.i18n import t
from app.models import (
    Category,
    Ingredient,
    Occasion,
    Season,
    ShoppingSection,
    Tag,
    WineCategory,
)
from app.models.wine import AGEING, BODY, PRICE_RANGES, SWEETNESS
from app.schemas.catalog import (
    CategoryOut,
    FacetValue,
    IngredientOut,
    OccasionOut,
    SeasonOut,
    ShoppingSectionOut,
    TagOut,
    WineCategoryOut,
    WineFacetsOut,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: DbSession) -> list[CategoryOut]:
    """The whole recipe category tree (Salado / Dulce / Bebidas → categories → subcategories)."""
    roots = db.scalars(
        select(Category).where(Category.parent_id.is_(None)).order_by(Category.position)
    ).all()
    return [CategoryOut.model_validate(r) for r in roots]


@router.get("/tags", response_model=list[TagOut])
def tags(db: DbSession, kind: str | None = None) -> list[TagOut]:
    q = select(Tag).order_by(Tag.kind, Tag.position)
    if kind:
        q = q.where(Tag.kind == kind)
    return [TagOut.model_validate(t) for t in db.scalars(q)]


@router.get("/seasons", response_model=list[SeasonOut])
def seasons(db: DbSession) -> list[SeasonOut]:
    return [SeasonOut.model_validate(s) for s in db.scalars(select(Season).order_by(Season.id))]


@router.get("/occasions", response_model=list[OccasionOut])
def occasions(db: DbSession) -> list[OccasionOut]:
    """Preloaded occasions. With a notebook's own ones: GET /occasions (login)."""
    q = select(Occasion).where(Occasion.notebook_id.is_(None)).order_by(Occasion.id)
    return [OccasionOut.model_validate(o) for o in db.scalars(q)]


@router.get("/shopping-sections", response_model=list[ShoppingSectionOut])
def shopping_sections(db: DbSession) -> list[ShoppingSectionOut]:
    q = select(ShoppingSection).order_by(ShoppingSection.position)
    return [ShoppingSectionOut.model_validate(s) for s in db.scalars(q)]


@router.get("/ingredients", response_model=list[IngredientOut])
def ingredients(
    db: DbSession,
    q: str = Query(min_length=1, description="Text to search in the name or aliases"),
    limit: int = Query(default=20, le=100),
) -> list[IngredientOut]:
    """Autocomplete for ingredient names ("pim" → pimentón dulce, pimienta negra...)."""
    term = f"%{q.strip().lower()}%"
    rows = db.scalars(
        select(Ingredient)
        .where(Ingredient.name.ilike(term) | Ingredient.aliases.ilike(term))
        .order_by(Ingredient.name)
        .limit(limit)
    )
    return [IngredientOut.model_validate(i) for i in rows]


@router.get("/wine-categories", response_model=list[WineCategoryOut])
def wine_categories(db: DbSession) -> list[WineCategoryOut]:
    """Wine type tree, two levels (Tintos → Tinto joven...), with serving temperature."""
    roots = db.scalars(
        select(WineCategory).where(WineCategory.parent_id.is_(None)).order_by(WineCategory.position)
    ).all()
    return [WineCategoryOut.model_validate(r) for r in roots]


def _facet(kind: str, codes) -> list[FacetValue]:
    return [
        FacetValue(code=c, name_es=t(f"{kind}.{c}", "es"), name_en=t(f"{kind}.{c}", "en"))
        for c in codes
    ]


@router.get("/wine-facets", response_model=WineFacetsOut)
def wine_facets() -> WineFacetsOut:
    """Values of the wine facets (sweetness, body, ageing, price) with their labels."""
    return WineFacetsOut(
        sweetness=_facet("wine_sweetness", SWEETNESS),
        body=_facet("wine_body", BODY),
        ageing=_facet("wine_ageing", AGEING),
        price_ranges=list(PRICE_RANGES),
    )
