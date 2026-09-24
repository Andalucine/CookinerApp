"""The demo cellar script imports each listed page once, with the type of the list."""

from sqlalchemy import select

from app.models import User, Wine
from app.services import importer, wine_importer
from scripts import import_demo_wines
from scripts.catalog_data.demo_wines import DEMO_WINES
from tests.services.test_wine_importer import SHEET, SHOP


def test_list_has_one_wine_per_type_and_valid_paths():
    slugs = [slug for _, slug in DEMO_WINES]
    assert len(slugs) == len(set(slugs)), "one example per type"
    assert all(path.endswith(".html") and not path.startswith("http") for path, _ in DEMO_WINES)


def test_imports_the_missing_wines_and_skips_the_rest(seeded, make_user, monkeypatch):
    make_user("Ana")
    user = seeded.scalar(select(User).where(User.email == "ana@example.com"))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    seeded.commit()

    pages = {
        "https://www.delatierra.com/a.html": SHEET,
        "https://www.delatierra.com/b.html": SHOP,
    }

    def fetch(url):
        if url not in pages:
            raise importer.FetchFailed
        return url, pages[url]

    monkeypatch.setattr(wine_importer, "fetch_html", fetch)
    wines = [("a.html", "blanco-aromatico"), ("b.html", "tinto-medio"), ("c.html", "cava")]

    added, failed = import_demo_wines.import_all(seeded, "ana@example.com", wines, echo=lambda s: 0)
    assert added == ["Zarate 2024", "Viña Tondonia Reserva 2012"]
    assert failed == ["https://www.delatierra.com/c.html"]
    saved = seeded.scalars(select(Wine).where(Wine.notebook_id == user.notebook.id)).all()
    assert {w.category.slug for w in saved} == {"blanco-aromatico", "tinto-medio"}
    zarate = next(w for w in saved if w.name == "Zarate 2024")
    assert zarate.winery == "Bodegas Zarate" and zarate.source_name == "Delatierra"
    assert float(zarate.source_price) == 15.13 and zarate.pairing_notes

    # Run again: nothing is duplicated
    added, _ = import_demo_wines.import_all(seeded, "ana@example.com", wines, echo=lambda s: 0)
    assert added == []


def test_main_refuses_a_free_notebook(seeded, make_user, capsys):
    make_user("Ana")
    assert import_demo_wines.main(["ana@example.com"], db=seeded) == 1
    assert "plan gratuito" in capsys.readouterr().out
    assert import_demo_wines.main(["nadie@example.com"], db=seeded) == 1
