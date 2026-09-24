"""Spice zone: list, cards, blends and the spices of a recipe (with what the pantry has)."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Ingredient,
    Notebook,
    NotebookBlend,
    PantryItem,
    Recipe,
    SpiceBlend,
    SpiceBlendItem,
    SpiceEquivalenceRule,
    SpiceSubstitution,
)
from app.schemas.catalog import local_text, texts
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
from app.services import blend as blend_service
from app.services import notebook_spice as own_service
from app.services import permissions

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


def families(
    db: Session, names: dict[str, dict[str, str]], notebook: Notebook | None = None
) -> list[SpiceFamilyOut]:
    counts = dict(
        db.execute(
            select(Ingredient.spice_family, func.count())
            .where(Ingredient.is_spice.is_(True))
            .group_by(Ingredient.spice_family)
        ).all()
    )
    if notebook:
        for own in own_service.list_for(db, notebook.id):
            counts[own.family] = counts.get(own.family, 0) + 1
        for b in blend_service.list_for(db, notebook.id):
            if b.ingredient_id not in _blend_ids(db) and not b.ingredient.is_spice:
                counts["blends"] = counts.get("blends", 0) + 1
    return [SpiceFamilyOut(code=f, **names[f], count=counts.get(f, 0)) for f in FAMILIES]


def _matches(ingredient: Ingredient, text: str | None) -> bool:
    if not text:
        return True
    term = text.strip().lower()
    return any(
        term in (value or "").lower()
        for value in (ingredient.name, ingredient.aliases, ingredient.name_en)
    )


def list_spices(
    db: Session, family: str | None, text: str | None, notebook: Notebook | None = None
) -> list[SpiceSummary]:
    """The catalogue; with a notebook, its versions are marked and its own blends added to
    the family "blends" (and to searches)."""
    own = blend_service.by_ingredient(db, notebook.id) if notebook else {}
    own_spices = own_service.by_ingredient(db, notebook.id) if notebook else {}
    own_subs = (
        own_service.ingredient_ids_with_own_substitutions(db, notebook.id) if notebook else set()
    )  # noqa: E501
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
    rows = [
        SpiceSummary(
            id=i.id,
            name=i.name,
            **texts(i, es=False),
            aliases=i.aliases,
            family=i.spice_family,
            has_substitutions=i.id in subs or i.id in own_subs,
            is_blend=i.id in blends,
            notebook_blend_id=own[i.id].id if i.id in own else None,
            is_own_version=i.id in own,
            added_by=permissions.added_by(notebook, own[i.id].created_by) if i.id in own else None,
        )
        for i in db.scalars(q.order_by(Ingredient.name))
    ]
    if notebook and family in (None, "blends"):
        catalogue = {r.id for r in rows} | blends
        for b in own.values():
            if b.ingredient_id in catalogue or not _matches(b.ingredient, text):
                continue
            rows.append(
                SpiceSummary(
                    id=b.ingredient_id,
                    name=b.ingredient.name,
                    **texts(b.ingredient, es=False),
                    aliases=b.ingredient.aliases,
                    family="blends",
                    has_substitutions=b.ingredient_id in subs,
                    is_blend=True,
                    notebook_blend_id=b.id,
                    is_own_version=False,
                    added_by=permissions.added_by(notebook, b.created_by),
                )
            )
    if notebook:
        catalogue = {r.id for r in rows}
        for sp in own_spices.values():
            if sp.ingredient_id in catalogue or (family and sp.family != family):
                continue
            if text and not (
                _matches(sp.ingredient, text) or (text.strip().lower() in (sp.aliases or ""))
            ):
                continue
            rows.append(
                SpiceSummary(
                    id=sp.ingredient_id,
                    name=sp.ingredient.name,
                    **texts(sp.ingredient, es=False),
                    aliases=sp.aliases,
                    family=sp.family,
                    has_substitutions=sp.ingredient_id in subs or sp.ingredient_id in own_subs,
                    is_blend=sp.ingredient_id in own,
                    notebook_blend_id=own[sp.ingredient_id].id if sp.ingredient_id in own else None,
                    notebook_spice_id=sp.id,
                    added_by=permissions.added_by(notebook, sp.created_by),
                )
            )
    if notebook:
        rows.sort(key=lambda r: r.name)
    return rows


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
        **texts(blend.ingredient, es=False),
        **texts(blend, "quick_substitute", "note"),
        items=[
            BlendItemOut(
                ingredient_id=it.ingredient_id,
                name=it.ingredient.name,
                **texts(it.ingredient, es=False),
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
                **texts(s, "substitute", "note"),
                substitute_id=s.substitute_id,
                ratio=s.ratio,
                in_my_pantry=(s.substitute_id in pantry)
                if pantry is not None and s.substitute_id
                else None,
            )
        )
    return out


def _first_blend(
    own: NotebookBlend | None, blend: SpiceBlend | None, notebook: Notebook | None
) -> BlendOut | None:
    if own is not None and notebook is not None:
        return blend_service.to_out(own, notebook)
    return _blend_out(blend) if blend else None


def card(
    db: Session, ingredient_id: int, notebook: Notebook | None = None, lang: str = "es"
) -> SpiceCard:
    """The card of a spice, or of a fresh ingredient that has substitutions (garlic, onion...),
    or of a blend of the notebook. The notebook's version of a blend comes first, with the
    catalogue's in `catalog_blend`."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise SpiceNotFound
    subs = _substitutions(db, [ingredient.id], None).get(ingredient.id, [])
    blend = db.scalar(_blend_query().where(SpiceBlend.ingredient_id == ingredient.id))
    own = (
        db.scalar(
            select(NotebookBlend).where(
                NotebookBlend.notebook_id == notebook.id,
                NotebookBlend.ingredient_id == ingredient.id,
            )
        )
        if notebook
        else None
    )
    if own is not None:
        own = blend_service.get(db, own.id)  # with its items loaded
    own_spice = own_service.by_ingredient(db, notebook.id).get(ingredient.id) if notebook else None
    own_subs_rows = (
        own_service.substitutions_for(db, notebook.id, [ingredient.id]).get(ingredient.id, [])
        if notebook
        else []
    )
    if own_subs_rows:
        subs = [own_service.substitution_out(r, None) for r in own_subs_rows]
    own_pairing = own_service.pairing_for(db, notebook.id, ingredient.id) if notebook else None
    if not ingredient.is_spice and not subs and blend is None and own is None and own_spice is None:
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
        **texts(ingredient, es=False),
        aliases=own_spice.aliases if own_spice else ingredient.aliases,
        family=own_spice.family if own_spice else ingredient.spice_family,
        notebook_spice_id=own_spice.id if own_spice else None,
        has_substitutions=bool(subs),
        has_own_substitutions=bool(own_subs_rows),
        substitutions_added_by=(
            permissions.added_by(notebook, own_subs_rows[0].created_by)
            if own_subs_rows and notebook
            else None
        ),
        pairs_with=(
            own_pairing.pairs_with if own_pairing else local_text(ingredient, lang, "pairs_with")
        ),
        has_own_pairs_with=own_pairing is not None,
        pairs_with_added_by=(
            permissions.added_by(notebook, own_pairing.created_by)
            if own_pairing and notebook
            else None
        ),
        is_blend=blend is not None or own is not None,
        notebook_blend_id=own.id if own else None,
        is_own_version=own is not None and blend is not None,
        added_by=(
            permissions.added_by(notebook, (own or own_spice).created_by)
            if (own or own_spice) and notebook
            else None
        ),
        substitutions=subs,
        blend=_first_blend(own, blend, notebook),
        catalog_blend=_blend_out(blend) if blend and own else None,
        used_in_blends=[
            BlendRef(ingredient_id=i.id, name=i.name, **texts(i, es=False)) for i in used_in
        ],
    )


def pantry_ids(db: Session, notebook_id: int) -> set[int]:
    return set(
        db.scalars(select(PantryItem.ingredient_id).where(PantryItem.notebook_id == notebook_id))
    )


def recipe_spices(db: Session, recipe: Recipe, my_notebook_id: int) -> list[RecipeSpiceOut]:
    """The ingredients of a recipe that have a card, in recipe order, checked against MY pantry."""
    subs_ids, blends = _with_substitutions(db), _blend_ids(db)
    blends |= set(blend_service.by_ingredient(db, recipe.notebook_id))  # the recipe's notebook
    own_spices = set(own_service.by_ingredient(db, recipe.notebook_id))
    subs_ids |= own_service.ingredient_ids_with_own_substitutions(db, recipe.notebook_id)
    wanted = [
        ri.ingredient
        for ri in recipe.ingredients
        if ri.ingredient.is_spice
        or ri.ingredient_id in subs_ids
        or ri.ingredient_id in blends
        or ri.ingredient_id in own_spices
    ]
    wanted = list({i.id: i for i in wanted}.values())  # drop repeats, keep order
    pantry = pantry_ids(db, my_notebook_id)
    subs = _substitutions(db, [i.id for i in wanted], pantry)
    own_subs = own_service.substitutions_for(db, recipe.notebook_id, [i.id for i in wanted])
    for ingredient_id, rows in own_subs.items():
        subs[ingredient_id] = [own_service.substitution_out(r, pantry) for r in rows]
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
