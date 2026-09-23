"""Spice zone: list, cards, blends and the spices of a recipe (with what the pantry has)."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Ingredient,
    PantryItem,
    Recipe,
    SpiceBlend,
    SpiceBlendItem,
    SpiceEquivalenceRule,
    SpiceSubstitution,
)
from app.schemas.spice import (
    BlendItemOut,
    BlendOut,
    BlendRef,
    EquivalenceRuleOut,
    RecipeSpiceOut,
    SpiceCard,
    SpiceFamilyOut,
    SpiceSummary,
    SubstitutionOut,
)

# Order in which the families are shown (same as the approved document)
FAMILIES = (
    "herbs",
    "seeds",
    "barks_roots_flowers",
    "peppers_chillies",
    "paprikas",
    "blends",
    "salts_seasonings",
)


class SpiceNotFound(Exception):
    pass


def _with_substitutions(db: Session) -> set[int]:
    return set(db.scalars(select(SpiceSubstitution.ingredient_id).distinct()))


def _blend_ids(db: Session) -> set[int]:
    return set(db.scalars(select(SpiceBlend.ingredient_id)))


def families(db: Session, names: dict[str, tuple[str, str]]) -> list[SpiceFamilyOut]:
    counts = dict(
        db.execute(
            select(Ingredient.spice_family, func.count())
            .where(Ingredient.is_spice.is_(True))
            .group_by(Ingredient.spice_family)
        ).all()
    )
    return [
        SpiceFamilyOut(code=f, name_es=names[f][0], name_en=names[f][1], count=counts.get(f, 0))
        for f in FAMILIES
    ]


def list_spices(db: Session, family: str | None, text: str | None) -> list[SpiceSummary]:
    q = select(Ingredient).where(Ingredient.is_spice.is_(True))
    if family:
        q = q.where(Ingredient.spice_family == family)
    if text:
        term = f"%{text.strip().lower()}%"
        q = q.where(
            or_(
                Ingredient.name.ilike(term),
                Ingredient.aliases.ilike(term),
                Ingredient.name_en.ilike(term),
            )
        )
    subs, blends = _with_substitutions(db), _blend_ids(db)
    return [
        SpiceSummary(
            id=i.id,
            name=i.name,
            name_en=i.name_en,
            aliases=i.aliases,
            family=i.spice_family,
            has_substitutions=i.id in subs,
            is_blend=i.id in blends,
        )
        for i in db.scalars(q.order_by(Ingredient.name))
    ]


def rules(db: Session) -> list[EquivalenceRuleOut]:
    rows = db.scalars(select(SpiceEquivalenceRule).order_by(SpiceEquivalenceRule.position))
    return [EquivalenceRuleOut.model_validate(r) for r in rows]


def _blend_query():
    return select(SpiceBlend).options(
        selectinload(SpiceBlend.ingredient),
        selectinload(SpiceBlend.items).selectinload(SpiceBlendItem.ingredient),
    )


def _blend_out(blend: SpiceBlend) -> BlendOut:
    return BlendOut(
        id=blend.id,
        ingredient_id=blend.ingredient_id,
        name=blend.ingredient.name,
        name_en=blend.ingredient.name_en,
        quick_substitute_es=blend.quick_substitute_es,
        quick_substitute_en=blend.quick_substitute_en,
        note_es=blend.note_es,
        note_en=blend.note_en,
        items=[
            BlendItemOut(
                ingredient_id=it.ingredient_id,
                name=it.ingredient.name,
                name_en=it.ingredient.name_en,
                parts=it.parts,
                is_optional=it.is_optional,
            )
            for it in blend.items
        ],
    )


def blends(db: Session) -> list[BlendOut]:
    rows = db.scalars(_blend_query()).all()
    return sorted((_blend_out(b) for b in rows), key=lambda b: b.name)


def _substitutions(
    db: Session, ingredient_ids: list[int], pantry: set[int] | None
) -> dict[int, list[SubstitutionOut]]:
    rows = db.scalars(
        select(SpiceSubstitution)
        .where(SpiceSubstitution.ingredient_id.in_(ingredient_ids))
        .order_by(SpiceSubstitution.ingredient_id, SpiceSubstitution.position)
    )
    out: dict[int, list[SubstitutionOut]] = {}
    for s in rows:
        out.setdefault(s.ingredient_id, []).append(
            SubstitutionOut(
                substitute_es=s.substitute_es,
                substitute_en=s.substitute_en,
                substitute_id=s.substitute_id,
                ratio=s.ratio,
                note_es=s.note_es,
                note_en=s.note_en,
                in_my_pantry=(s.substitute_id in pantry)
                if pantry is not None and s.substitute_id
                else None,
            )
        )
    return out


def card(db: Session, ingredient_id: int) -> SpiceCard:
    """The card of a spice, or of a fresh ingredient that has substitutions (garlic, onion...)."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise SpiceNotFound
    subs = _substitutions(db, [ingredient.id], None).get(ingredient.id, [])
    blend = db.scalar(_blend_query().where(SpiceBlend.ingredient_id == ingredient.id))
    if not ingredient.is_spice and not subs and blend is None:
        raise SpiceNotFound
    used_in = db.scalars(
        select(Ingredient)
        .join(SpiceBlend, SpiceBlend.ingredient_id == Ingredient.id)
        .join(SpiceBlendItem, SpiceBlendItem.blend_id == SpiceBlend.id)
        .where(SpiceBlendItem.ingredient_id == ingredient.id)
        .order_by(Ingredient.name)
    )
    return SpiceCard(
        id=ingredient.id,
        name=ingredient.name,
        name_en=ingredient.name_en,
        aliases=ingredient.aliases,
        family=ingredient.spice_family,
        has_substitutions=bool(subs),
        is_blend=blend is not None,
        substitutions=subs,
        blend=_blend_out(blend) if blend else None,
        used_in_blends=[
            BlendRef(ingredient_id=i.id, name=i.name, name_en=i.name_en) for i in used_in
        ],
    )


def pantry_ids(db: Session, notebook_id: int) -> set[int]:
    return set(
        db.scalars(select(PantryItem.ingredient_id).where(PantryItem.notebook_id == notebook_id))
    )


def recipe_spices(db: Session, recipe: Recipe, my_notebook_id: int) -> list[RecipeSpiceOut]:
    """The ingredients of a recipe that have a card, in recipe order, checked against MY pantry."""
    subs_ids, blends = _with_substitutions(db), _blend_ids(db)
    wanted = [
        ri.ingredient
        for ri in recipe.ingredients
        if ri.ingredient.is_spice or ri.ingredient_id in subs_ids or ri.ingredient_id in blends
    ]
    wanted = list({i.id: i for i in wanted}.values())  # drop repeats, keep order
    pantry = pantry_ids(db, my_notebook_id)
    subs = _substitutions(db, [i.id for i in wanted], pantry)
    return [
        RecipeSpiceOut(
            ingredient_id=i.id,
            name=i.name,
            in_my_pantry=i.id in pantry,
            substitutions=subs.get(i.id, []),
            is_blend=i.id in blends,
        )
        for i in wanted
    ]
