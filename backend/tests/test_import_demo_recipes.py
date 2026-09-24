"""The demo recipes script imports each listed page once, with the category, moment and
seasons of the list (session 9)."""

from sqlalchemy import select

from app.models import Recipe, User
from app.services import importer
from scripts import import_demo_recipes
from scripts.catalog_data.demo_recipes import DEMO_RECIPES, SITE
from scripts.seed_catalogs import run
from tests.services.test_importer import page


def test_list_is_fifty_everyday_recipes_with_valid_slugs(db_session):
    run(db_session)
    from app.models import Category, Season, Tag

    slugs = set(db_session.scalars(select(Category.slug)))
    courses = set(db_session.scalars(select(Tag.code).where(Tag.kind == "course")))
    seasons = set(db_session.scalars(select(Season.code)))
    paths = [p for p, _, _, _ in DEMO_RECIPES]
    assert len(paths) == len(set(paths)) >= 50
    for path, slug, course, recipe_seasons in DEMO_RECIPES:
        assert not path.startswith("http") and "/" in path, path
        assert slug in slugs, slug
        assert course is None or course in courses, course
        assert set(recipe_seasons) <= seasons, recipe_seasons
    mains = [c for _, _, c, _ in DEMO_RECIPES if c in ("main", "light-dinner")]
    assert len(mains) >= 40  # enough plates for a week of lunches and dinners


def test_imports_the_missing_recipes_and_skips_the_rest(seeded, make_user, monkeypatch):
    make_user("Ana")
    user = seeded.scalar(select(User).where(User.email == "ana@example.com"))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    seeded.commit()

    pages = {SITE + "a/lentejas": page(), SITE + "b/otra": page().replace("Lentejas", "Otra")}

    def fetch(url):
        if url not in pages:
            raise importer.FetchFailed
        return url, pages[url]

    monkeypatch.setattr(importer, "fetch_html", fetch)
    recipes = [
        ("a/lentejas", "guisos-legumbres", "main", ["winter"]),
        ("b/otra", "sopas-frias", "light-dinner", []),
        ("c/nada", "pasta-salsa", "main", []),
    ]
    added, failed = import_demo_recipes.import_all(
        seeded, "ana@example.com", recipes, echo=lambda s: 0
    )
    assert len(added) == 2 and failed == [SITE + "c/nada"]
    saved = seeded.scalars(select(Recipe).where(Recipe.notebook_id == user.notebook.id)).all()
    assert len(saved) == 2
    first = next(r for r in saved if r.source_url == SITE + "a/lentejas")
    assert [c.category.slug for c in first.categories] == ["guisos-legumbres"]
    assert [t.code for t in first.tags] == ["main"]
    assert [s.code for s in first.seasons] == ["winter"]
    assert first.source_type == "web" and first.source_name

    # running it again adds nothing
    again, _ = import_demo_recipes.import_all(seeded, "ana@example.com", recipes, echo=lambda s: 0)
    assert again == []
