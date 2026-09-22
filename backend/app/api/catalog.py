"""Global catalogues the app needs to show pickers: read-only, no login required."""

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import DbSession
from app.models import Category, Ingredient, Occasion, Season, ShoppingSection, Tag
from app.schemas.catalog import (
    CategoryOut,
    IngredientOut,
    OccasionOut,
    SeasonOut,
    ShoppingSectionOut,
    TagOut,
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
    """Preloaded occasions (a notebook's own ones come with the notebook, later)."""
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
