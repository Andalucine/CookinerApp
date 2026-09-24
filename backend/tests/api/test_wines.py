from sqlalchemy import select

from app.models import User, WineCategory
from tests.api.test_recipes import _cat, marmitako


def _wtype(db, slug):
    return db.scalar(select(WineCategory).where(WineCategory.slug == slug)).id


def _paid(db, email):
    user = db.scalar(select(User).where(User.email == email))
    user.plan, user.max_recipes, user.max_shared_with = "individual", None, 2
    db.commit()


def _wine(db, name, slug, **extra):
    return {"name": name, "category_id": _wtype(db, slug), **extra}


def test_wine_catalogue(client, seeded):
    tree = client.get("/catalog/wine-categories").json()
    assert [t["slug"] for t in tree][:2] == ["tintos", "blancos"]
    assert tree[0]["serving_temp"] == "14–18 °C" and len(tree[0]["children"]) == 4
    facets = client.get("/catalog/wine-facets").json()
    assert facets["body"][2] == {"code": "full", "name_es": "Con cuerpo", "name_en": "Full-bodied"}
    assert facets["price_ranges"] == ["€", "€€", "€€€", "€€€€"]


def test_free_notebook_has_no_wine_section(client, seeded, make_user):
    h, _ = make_user()
    r = client.get("/wines", headers=h)
    assert r.status_code == 403 and "plan" in r.json()["detail"]
    assert client.post("/wines", json={"name": "Viña Tondonia"}, headers=h).status_code == 403
    rid = client.post("/recipes", json=marmitako(seeded), headers=h).json()["id"]
    assert client.get(f"/recipes/{rid}/wines", headers=h).status_code == 403


def test_wines_crud_search_and_favorites(client, seeded, make_user):
    h, _ = make_user()
    _paid(seeded, "ana@example.com")
    body = _wine(
        seeded, "Viña Tondonia Reserva", "tinto-cuerpo-crianza", winery="López de Heredia",
        appellation="D.O.Ca. Rioja", grapes="tempranillo, garnacha", ageing="reserva",
        body="full", sweetness="dry", vintage=2012, price_range="€€€",
    )  # fmt: skip
    r = client.post("/wines", json=body, headers=h)
    assert r.status_code == 201, r.text
    wine = r.json()
    assert wine["category"]["parent"]["name_es"] == "Tintos"
    assert wine["category"]["serving_temp"] == "14–18 °C"
    client.post("/wines", json=_wine(seeded, "Pazo de Señoráns", "blanco-aromatico"), headers=h)

    # Facet validation and unknown type
    bad = {**body, "body": "enorme"}
    assert client.post("/wines", json=bad, headers=h).status_code == 422
    assert (
        client.post("/wines", json={"name": "x", "category_id": 99999}, headers=h).status_code
        == 422
    )

    # Search: a first-level type includes its children; text; facets
    tintos = client.get("/catalog/wine-categories").json()[0]["id"]
    assert [
        w["name"] for w in client.get(f"/wines?category_id={tintos}", headers=h).json()["items"]
    ] == ["Viña Tondonia Reserva"]
    assert client.get("/wines?q=garnacha", headers=h).json()["total"] == 1
    assert client.get("/wines?appellation=rioja&ageing=reserva", headers=h).json()["total"] == 1
    assert client.get("/wines", headers=h).json()["total"] == 2

    # Favourites
    client.post(f"/wines/{wine['id']}/favorite", headers=h)
    favs = client.get("/wines?favorites=true", headers=h).json()["items"]
    assert [w["id"] for w in favs] == [wine["id"]] and favs[0]["is_favorite"]
    client.delete(f"/wines/{wine['id']}/favorite", headers=h)
    assert client.get("/wines?favorites=true", headers=h).json()["total"] == 0

    r = client.put(f"/wines/{wine['id']}", json={**body, "vintage": 2014}, headers=h)
    assert r.json()["vintage"] == 2014 and r.json()["edited_by"] is None
    assert client.delete(f"/wines/{wine['id']}", headers=h).status_code == 200
    assert client.get(f"/wines/{wine['id']}", headers=h).status_code == 404


def test_recipe_wines_and_automatic_suggestion(client, seeded, make_user):
    h, _ = make_user()
    _paid(seeded, "ana@example.com")
    stew = marmitako(
        seeded, title="Cocido", category_ids=[_cat(seeded, "cocidos-potajes")], tag_ids=[]
    )
    rid = client.post("/recipes", json=stew, headers=h).json()["id"]
    young = client.post(
        "/wines", json=_wine(seeded, "Tinto joven de casa", "tinto-joven"), headers=h
    )
    client.post("/wines", json=_wine(seeded, "Oloroso Don Nuño", "oloroso"), headers=h)
    client.post("/wines", json=_wine(seeded, "Albariño", "blanco-aromatico"), headers=h)

    # No wines of its own: suggestion from the parent category (cocidos-potajes → legumbres)
    body = client.get(f"/recipes/{rid}/wines", headers=h).json()
    assert body["recommended"] == []
    sug = body["suggestion"]
    assert sug["based_on"]["name_es"] and _cat(seeded, "legumbres") == sug["based_on"]["id"]
    assert [w["wine_category"]["slug"] for w in sug["wine_types"]] == [
        "tinto-joven", "tinto-medio", "oloroso", "amontillado",
    ]  # fmt: skip
    assert "oloroso" in sug["wine_types"][0]["reason_es"]
    assert [w["name"] for w in sug["my_wines"]] == ["Tinto joven de casa", "Oloroso Don Nuño"]

    # Recommending a wine replaces the suggestion; sending it again updates the reason
    wid = young.json()["id"]
    r = client.post(
        f"/recipes/{rid}/wines", json={"wine_id": wid, "reason": "El de siempre"}, headers=h
    )
    assert r.status_code == 201 and r.json()["suggestion"] is None
    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": wid, "reason": "Fresco"}, headers=h)
    rec = r.json()["recommended"]
    assert len(rec) == 1 and rec[0]["reason"] == "Fresco" and rec[0]["origin"] == "manual"

    # Removing it brings the suggestion back; the wine stays in the notebook
    assert client.delete(f"/recipes/{rid}/wines/{rec[0]['id']}", headers=h).status_code == 200
    assert client.get(f"/recipes/{rid}/wines", headers=h).json()["suggestion"] is not None
    assert client.get(f"/wines/{wid}", headers=h).status_code == 200


def test_wines_roles_and_free_guest(client, seeded, make_user, share):
    ana_h, _ = make_user("Ana")
    luis_h, _ = make_user("Luis")  # free plan, editor in Ana's paid notebook
    eva_h, _ = make_user("Eva")
    nb = share(ana_h, "ana@example.com", luis_h, role="editor")
    share(ana_h, "ana@example.com", eva_h, role="viewer")
    rid = client.post("/recipes", json=marmitako(seeded), headers=ana_h).json()["id"]
    ana_wine = client.post("/wines", json=_wine(seeded, "Txakoli", "aguja"), headers=ana_h).json()

    # The free editor uses the wine section of Ana's notebook (it follows the owner's plan)
    r = client.post(
        "/wines", json={**_wine(seeded, "Fino Inocente", "fino-manzanilla"), "notebook_id": nb},
        headers=luis_h,
    )  # fmt: skip
    assert r.status_code == 201 and r.json()["added_by"] == "Luis"
    luis_wine = r.json()
    r = client.put(f"/wines/{ana_wine['id']}", json={"name": "Txakoli Ameztoi"}, headers=luis_h)
    assert r.json()["edited_by"] == "Luis"
    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": luis_wine["id"]}, headers=luis_h)
    link = r.json()["recommended"][0]
    assert link["added_by"] == "Luis"
    # ...but his own free notebook still has no wine section
    assert client.get("/wines", headers=luis_h).status_code == 403
    # An editor cannot delete the owner's wine; the owner can delete the editor's link
    assert client.delete(f"/wines/{ana_wine['id']}", headers=luis_h).status_code == 403
    assert client.delete(f"/recipes/{rid}/wines/{link['id']}", headers=ana_h).status_code == 200

    # Viewer: sees and stars, does not write
    assert client.get(f"/wines?notebook_id={nb}", headers=eva_h).json()["total"] == 2
    assert client.post(f"/wines/{ana_wine['id']}/favorite", headers=eva_h).status_code == 200
    assert (
        client.put(f"/wines/{ana_wine['id']}", json={"name": "x"}, headers=eva_h).status_code == 404
    )
    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": ana_wine["id"]}, headers=eva_h)
    assert r.status_code == 404

    # A wine from another notebook cannot be recommended; strangers see nothing
    pepe_h, _ = make_user("Pepe")
    _paid(seeded, "pepe@example.com")
    other = client.post("/wines", json={"name": "Otro"}, headers=pepe_h).json()
    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": other["id"]}, headers=ana_h)
    assert r.status_code == 422
    assert client.get(f"/wines/{ana_wine['id']}", headers=pepe_h).status_code == 404
    assert client.get(f"/wines?notebook_id={nb}", headers=pepe_h).status_code == 404


def test_category_counts_and_recipes_of_a_wine(client, seeded, make_user):
    h, _ = make_user()
    _paid(seeded, "ana@example.com")
    tinto = client.post(
        "/wines", json=_wine(seeded, "Tondonia", "tinto-cuerpo-crianza"), headers=h
    ).json()
    client.post("/wines", json=_wine(seeded, "Señoráns", "blanco-aromatico"), headers=h)
    tintos = client.get("/catalog/wine-categories").json()[0]
    counts = {
        c["category_id"]: c["count"] for c in client.get("/wines/category-counts", headers=h).json()
    }
    assert counts[tintos["id"]] == 1 and counts[tinto["category"]["id"]] == 1
    assert sum(counts.values()) == 4  # two wines, each in its type and its parent type

    from tests.api.test_recipes import marmitako

    rid = client.post("/recipes", json=marmitako(seeded), headers=h).json()["id"]
    client.post(
        f"/recipes/{rid}/wines",
        json={"wine_id": tinto["id"], "reason": "Va con el atún"},
        headers=h,
    )
    recipes = client.get(f"/wines/{tinto['id']}/recipes", headers=h).json()
    assert [(r["recipe_id"], r["reason"]) for r in recipes] == [(rid, "Va con el atún")]
    assert client.get(f"/wines/{tinto['id']}/recipes").status_code == 401
