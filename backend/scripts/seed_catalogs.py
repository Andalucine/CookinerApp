"""Load (or refresh) the global catalogues: seasons, occasions, shopping sections, category tree,
tags, spices, equivalence rules, substitutions, blends, wine types and pairing rules.

Run from `backend/`:  python -m scripts.seed_catalogs

Safe to run as many times as you like:
- Rows referenced by user data (categories, tags, ingredients, wine types, seasons, occasions,
  sections) are matched by their natural key and updated in place, never deleted.
- Pure catalogue content (equivalence rules, substitutions, blend items, pairing rules) is
  replaced entirely, so editing the data files and re-running is the way to correct it.
"""

import logging
import sys

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Category,
    Ingredient,
    Occasion,
    PairingRule,
    Season,
    ShoppingSection,
    SpiceBlend,
    SpiceBlendItem,
    SpiceEquivalenceRule,
    SpiceSubstitution,
    Tag,
    WineCategory,
)
from scripts.catalog_data import basics, categories, spices, wines

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed")


def _upsert(db: Session, model, keys: dict, values: dict):
    """Find the row by `keys`; create it or update `values`. Returns the row."""
    row = db.scalar(select(model).filter_by(**keys))
    if row is None:
        row = model(**keys, **values)
        db.add(row)
        db.flush()
    else:
        for k, v in values.items():
            setattr(row, k, v)
    return row


def seed_basics(db: Session) -> None:
    for code, es, en in basics.SEASONS:
        _upsert(db, Season, {"code": code}, {"name_es": es, "name_en": en})
    for es, en in basics.OCCASIONS:
        _upsert(
            db,
            Occasion,
            {"notebook_id": None, "name_es": es},
            {"name_en": en, "is_preloaded": True},
        )
    for pos, (code, es, en) in enumerate(basics.SHOPPING_SECTIONS):
        _upsert(
            db, ShoppingSection, {"code": code}, {"name_es": es, "name_en": en, "position": pos}
        )
    for kind, values in basics.TAGS.items():
        for pos, (code, es, en) in enumerate(values):
            _upsert(
                db,
                Tag,
                {"kind": kind, "code": code},
                {"name_es": es, "name_en": en, "position": pos},
            )
    log.info("Estaciones, épocas, secciones de compra y etiquetas: ok")


def seed_categories(db: Session) -> None:
    count = 0
    for pos1, (slug, es, en, branches) in enumerate(categories.TREE):
        root = _upsert(
            db,
            Category,
            {"parent_id": None, "slug": slug},
            {
                "name_es": es,
                "name_en": en,
                "level": 1,
                "position": pos1,
                "is_preloaded": True,
                "notebook_id": None,
            },
        )
        count += 1
        for pos2, (slug2, es2, en2, ex2, children) in enumerate(branches):
            cat = _upsert(
                db,
                Category,
                {"parent_id": root.id, "slug": slug2},
                {
                    "name_es": es2,
                    "name_en": en2,
                    "examples_es": ex2,
                    "level": 2,
                    "position": pos2,
                    "is_preloaded": True,
                    "notebook_id": None,
                },
            )
            count += 1
            for pos3, (slug3, es3, en3, ex3) in enumerate(children):
                _upsert(
                    db,
                    Category,
                    {"parent_id": cat.id, "slug": slug3},
                    {
                        "name_es": es3,
                        "name_en": en3,
                        "examples_es": ex3,
                        "level": 3,
                        "position": pos3,
                        "is_preloaded": True,
                        "notebook_id": None,
                    },
                )
                count += 1
    log.info("Categorías de recetas: %d", count)


def seed_ingredients(db: Session) -> dict[str, Ingredient]:
    """Spices and the fresh ingredients the substitution table mentions. Returns name → row."""
    sections = {s.code: s for s in db.scalars(select(ShoppingSection))}
    by_name: dict[str, Ingredient] = {}
    for family, items in spices.SPICES.items():
        for name, name_en, aliases in items:
            row = _upsert(
                db,
                Ingredient,
                {"name": name},
                {
                    "name_en": name_en,
                    "aliases": aliases,
                    "is_spice": True,
                    "spice_family": family,
                    "shopping_section_id": sections["spices"].id,
                },
            )
            by_name[name] = row
    for name, name_en, aliases, section in spices.FRESH_INGREDIENTS:
        row = _upsert(
            db,
            Ingredient,
            {"name": name},
            {"name_en": name_en, "aliases": aliases, "shopping_section_id": sections[section].id},
        )
        by_name[name] = row
    log.info("Ingredientes del catálogo (especias y básicos): %d", len(by_name))
    return by_name


def seed_spice_zone(db: Session, ing: dict[str, Ingredient]) -> None:
    db.execute(delete(SpiceEquivalenceRule))
    for pos, (s_es, s_en, e_es, e_en, n_es, n_en) in enumerate(spices.EQUIVALENCE_RULES):
        db.add(
            SpiceEquivalenceRule(
                situation_es=s_es,
                situation_en=s_en,
                equivalence_es=e_es,
                equivalence_en=e_en,
                note_es=n_es,
                note_en=n_en,
                position=pos,
            )
        )

    db.execute(delete(SpiceSubstitution))
    n_subs = 0
    for missing, options in spices.SUBSTITUTIONS.items():
        for pos, (sub_es, sub_en, ratio, n_es, n_en, linked) in enumerate(options):
            db.add(
                SpiceSubstitution(
                    ingredient_id=ing[missing].id,
                    substitute_es=sub_es,
                    substitute_en=sub_en,
                    substitute_id=ing[linked].id if linked else None,
                    ratio=ratio,
                    note_es=n_es,
                    note_en=n_en,
                    position=pos,
                )
            )
            n_subs += 1

    n_items = 0
    for blend_name, (quick_es, quick_en, note_es, items) in spices.BLENDS.items():
        blend = _upsert(
            db,
            SpiceBlend,
            {"ingredient_id": ing[blend_name].id},
            {"quick_substitute_es": quick_es, "quick_substitute_en": quick_en, "note_es": note_es},
        )
        db.execute(delete(SpiceBlendItem).where(SpiceBlendItem.blend_id == blend.id))
        for pos, (name, parts, optional) in enumerate(items):
            db.add(
                SpiceBlendItem(
                    blend_id=blend.id,
                    ingredient_id=ing[name].id,
                    parts=parts,
                    is_optional=optional,
                    position=pos,
                )
            )
            n_items += 1
    log.info(
        "Reglas de equivalencia: %d · sustituciones: %d · mezclas: %d (%d ingredientes)",
        len(spices.EQUIVALENCE_RULES),
        n_subs,
        len(spices.BLENDS),
        n_items,
    )


def seed_wines(db: Session) -> None:
    by_slug: dict[str, WineCategory] = {}
    for pos, (slug, es, en, temp, children) in enumerate(wines.WINE_TREE):
        root = _upsert(
            db,
            WineCategory,
            {"parent_id": None, "slug": slug},
            {"name_es": es, "name_en": en, "serving_temp": temp, "position": pos},
        )
        by_slug[slug] = root
        for pos2, (slug2, es2, en2, ex2) in enumerate(children):
            by_slug[slug2] = _upsert(
                db,
                WineCategory,
                {"parent_id": root.id, "slug": slug2},
                {
                    "name_es": es2,
                    "name_en": en2,
                    "examples_es": ex2,
                    "serving_temp": temp,
                    "position": pos2,
                },
            )
    log.info("Tipos de vino: %d", len(by_slug))

    recipe_cats = {c.slug: c for c in db.scalars(select(Category).where(Category.level > 1))}
    db.execute(delete(PairingRule))
    n = 0
    for recipe_slug, wine_slugs, reason_es, reason_en in wines.PAIRING_RULES:
        for pos, wine_slug in enumerate(wine_slugs):
            db.add(
                PairingRule(
                    recipe_category_id=recipe_cats[recipe_slug].id,
                    wine_category_id=by_slug[wine_slug].id,
                    reason_es=reason_es,
                    reason_en=reason_en,
                    position=pos,
                )
            )
            n += 1
    log.info("Reglas de maridaje: %d", n)


def run(db: Session) -> None:
    seed_basics(db)
    seed_categories(db)
    ingredients = seed_ingredients(db)
    seed_spice_zone(db, ingredients)
    seed_wines(db)
    db.commit()
    log.info("Catálogos cargados.")


if __name__ == "__main__":
    with SessionLocal() as session:
        try:
            run(session)
        except Exception:
            session.rollback()
            log.exception("Error cargando los catálogos; no se ha guardado nada")
            sys.exit(1)
