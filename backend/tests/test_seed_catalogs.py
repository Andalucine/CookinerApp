from sqlalchemy import func, select

from app.models import Category, Ingredient, PairingRule, SpiceSubstitution, Tag, WineCategory
from scripts.seed_catalogs import run


def _count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_loads_catalogs_and_is_idempotent(db_session):
    run(db_session)
    first = {m: _count(db_session, m) for m in (Category, Ingredient, Tag, WineCategory)}
    assert first[Category] == 153  # 3 branches + categories + subcategories
    assert first[Tag] == 40
    assert first[WineCategory] == 40
    assert _count(db_session, SpiceSubstitution) == 175
    assert _count(db_session, PairingRule) > 50

    run(db_session)  # second run: nothing duplicated
    assert {m: _count(db_session, m) for m in first} == first
    assert _count(db_session, SpiceSubstitution) == 175


def test_tree_has_three_levels_and_no_world_cuisine_branch(db_session):
    run(db_session)
    roots = db_session.scalars(select(Category).where(Category.parent_id.is_(None))).all()
    assert sorted(r.slug for r in roots) == ["bebidas", "dulce", "salado"]
    assert db_session.scalar(select(Category).where(Category.slug == "cocina-del-mundo")) is None
    origin_tags = db_session.scalars(select(Tag).where(Tag.kind == "origin")).all()
    assert len(origin_tags) == 10


def test_spices_link_to_their_section_and_substitutes(db_session):
    run(db_session)
    pimenton = db_session.scalar(select(Ingredient).where(Ingredient.name == "pimentón dulce"))
    assert pimenton.is_spice and pimenton.shopping_section.code == "spices"
    subs = db_session.scalars(
        select(SpiceSubstitution).where(SpiceSubstitution.ingredient_id == pimenton.id)
    ).all()
    assert [s.substitute_es for s in subs][:2] == [
        "Pimentón de la Vera dulce",
        "Ñora o choricero (pulpa)",
    ]
    assert subs[0].substitute.name == "pimentón de la vera"


def test_occasion_taken_out_of_the_list_is_deleted(db_session):
    from app.models import Occasion, Recipe, RecipeOccasion

    run(db_session)
    names = db_session.scalars(select(Occasion.name_es).where(Occasion.notebook_id.is_(None))).all()
    assert "Verano" not in names  # a season, not an occasion (session 7)
    assert "Feria" not in names
    assert sorted(names) == ["Cuaresma", "Navidad", "Semana Santa", "Todos los Santos"]

    # An old database still has it, linked to a recipe: running the seed again removes both
    old = Occasion(name_es="Verano", name_en="Summer holidays", is_preloaded=True)
    db_session.add(old)
    db_session.flush()
    recipe = db_session.scalars(select(Recipe)).first()
    if recipe is not None:
        db_session.add(RecipeOccasion(recipe_id=recipe.id, occasion_id=old.id))
    old_id = old.id
    db_session.commit()
    run(db_session)
    assert db_session.scalar(select(Occasion).where(Occasion.id == old_id)) is None
    assert not db_session.scalars(
        select(RecipeOccasion).where(RecipeOccasion.occasion_id == old_id)
    ).all()
