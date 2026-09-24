import pytest
from sqlalchemy import select

from app.models import ImportJob, User
from app.services import importer
from tests.services.test_importer import page

URL = "https://ejemplo.test/lentejas"


@pytest.fixture
def fake_web(monkeypatch):
    """Serve the test page instead of going to the internet."""
    pages = {URL: page()}

    def fetch(url):
        if url not in pages:
            raise importer.FetchFailed
        return url, pages[url]

    monkeypatch.setattr(importer, "fetch_html", fetch)
    return pages


def _paid(db, email):
    user = db.scalar(select(User).where(User.email == email))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    db.commit()


def test_free_notebook_cannot_import(client, seeded, make_user, fake_web):
    h, _ = make_user()
    r = client.post("/imports/recipe", json={"url": URL}, headers=h)
    assert r.status_code == 403 and "plan" in r.json()["detail"]


def test_preview_then_save_keeps_the_source(client, seeded, make_user, fake_web):
    h, user = make_user()
    _paid(seeded, "ana@example.com")
    r = client.post("/imports/recipe", json={"url": URL}, headers=h)
    assert r.status_code == 200, r.text
    preview = r.json()
    assert preview["complete"] and preview["warnings"] == []
    draft = preview["recipe"]
    assert draft["source_type"] == "web" and draft["source_url"] == URL
    assert draft["source_name"] == "Cocina de Prueba" and draft["cook_name"] == "Marta Prueba"
    # Names matched against the catalogue: "ajo picados" → ajo, "Sal" → sal and, with the
    # everyday catalogue (session 9), "lentejas pardinas" → lenteja
    names = [i["name"] for i in draft["ingredients"]]
    assert names == ["lenteja", "ajo", "pimentón dulce", "sal"]
    # Nothing saved yet
    assert client.get("/recipes", headers=h).json()["total"] == 0

    draft["title"] = "Lentejas de Marta"  # the user edits the preview
    r = client.post(f"/imports/{preview['job_id']}/save", json=draft, headers=h)
    assert r.status_code == 201, r.text
    recipe = r.json()
    assert recipe["title"] == "Lentejas de Marta" and recipe["source_url"] == URL
    assert recipe["youtube_url"] == "https://www.youtube.com/watch?v=abcdefghijk"
    assert recipe["notebook_id"] == user["notebook_id"]
    # Saved once only; history shows it
    r = client.post(f"/imports/{preview['job_id']}/save", json=draft, headers=h)
    assert r.status_code == 409
    history = client.get("/imports", headers=h).json()
    assert history[0]["status"] == "ok" and history[0]["recipe_id"] == recipe["id"]
    # The source link cannot be dropped
    job2 = client.post("/imports/recipe", json={"url": URL}, headers=h).json()
    bad = {**job2["recipe"], "source_url": None}
    assert client.post(f"/imports/{job2['job_id']}/save", json=bad, headers=h).status_code == 422


def test_errors_are_recorded(client, seeded, make_user, fake_web):
    h, _ = make_user()
    _paid(seeded, "ana@example.com")
    r = client.post("/imports/recipe", json={"url": "https://ejemplo.test/no-existe"}, headers=h)
    assert r.status_code == 502 and "abrir" in r.json()["detail"]
    fake_web["https://ejemplo.test/vacia"] = "<html><body>sin receta</body></html>"
    r = client.post("/imports/recipe", json={"url": "https://ejemplo.test/vacia"}, headers=h)
    assert r.status_code == 422
    jobs = seeded.scalars(select(ImportJob).order_by(ImportJob.id)).all()
    assert [(j.status, j.error_message) for j in jobs] == [
        ("error", "FetchFailed"), ("error", "NoRecipeFound"),
    ]  # fmt: skip


def test_free_editor_imports_into_paid_notebook(client, seeded, make_user, share, fake_web):
    ana_h, _ = make_user("Ana")
    luis_h, _ = make_user("Luis")
    eva_h, _ = make_user("Eva")
    nb = share(ana_h, "ana@example.com", luis_h, role="editor")
    share(ana_h, "ana@example.com", eva_h, role="viewer")
    r = client.post("/imports/recipe", json={"url": URL, "notebook_id": nb}, headers=luis_h)
    assert r.status_code == 200
    preview = r.json()
    r = client.post(f"/imports/{preview['job_id']}/save", json=preview["recipe"], headers=luis_h)
    assert r.status_code == 201 and r.json()["added_by"] == "Luis"
    # Not into his own free notebook, and a viewer cannot import; others cannot use his job
    assert client.post("/imports/recipe", json={"url": URL}, headers=luis_h).status_code == 403
    r = client.post("/imports/recipe", json={"url": URL, "notebook_id": nb}, headers=eva_h)
    assert r.status_code == 404
    r = client.post(f"/imports/{preview['job_id']}/save", json=preview["recipe"], headers=ana_h)
    assert r.status_code == 404


def test_import_wine_preview(client, seeded, make_user, monkeypatch):
    from sqlalchemy import select

    from app.models import User
    from app.services import wine_importer
    from tests.services.test_wine_importer import SHOP

    h, _ = make_user("Ana")
    user = seeded.scalar(select(User).where(User.email == "ana@example.com"))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    seeded.commit()
    monkeypatch.setattr(wine_importer, "fetch_html", lambda url: (url, SHOP))

    r = client.post("/imports/wine", json={"url": "https://www.delatierra.com/x.html"}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["complete"] and body["warnings"] == []
    wine = body["wine"]
    assert wine["name"] == "Viña Tondonia Reserva 2012" and wine["category_id"]
    assert wine["source_url"] == "https://www.delatierra.com/x.html"
    assert wine["source_name"] == "Delatierra" and wine["source_price"] == 38.9
    assert "Cordero" in wine["pairing_notes"] or "cordero" in wine["pairing_notes"].lower()
    # The preview is saved through the normal route, keeping the link
    saved = client.post("/wines", json=wine, headers=h)
    assert saved.status_code == 201, saved.text
    assert saved.json()["category"]["parent"]["name_es"] == "Tintos"
    assert saved.json()["source_url"].startswith("https://www.delatierra.com")
    assert saved.json()["source_price"] == 38.9
    assert [c["name_es"] for c in saved.json()["pairs_with_categories"]]


def test_import_wine_needs_a_paid_plan(client, seeded, make_user):
    h, _ = make_user("Ana")
    r = client.post("/imports/wine", json={"url": "https://shop.test/x"}, headers=h)
    assert r.status_code == 403
