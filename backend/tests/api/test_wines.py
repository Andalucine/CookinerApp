"""The shop's cellar (session 9: Vinoselección): the same wines for every notebook and plan."""

from sqlalchemy import select

from app.models import WineCategory
from app.schemas.wine import WineIn
from app.services import wine as wine_service
from tests.api.test_recipes import _cat, marmitako

SHOP = "https://www.vinoseleccion.com/"


def _wtype(db, slug):
    return db.scalar(select(WineCategory).where(WineCategory.slug == slug)).id


def _shop_wine(db, name, slug, *, in_stock=True, **extra):
    """A wine as the sync script leaves it."""
    data = WineIn(
        name=name,
        category_id=_wtype(db, slug),
        source_url=SHOP + name.lower().replace(" ", "-"),
        source_price=extra.pop("source_price", 12.5),
        **extra,
    )
    wine, _ = wine_service.upsert(db, data)
    wine.in_stock = in_stock
    db.commit()
    return wine


def test_wine_catalogue(client, seeded):
    tree = client.get("/catalog/wine-categories").json()
    assert [t["slug"] for t in tree][:2] == ["tintos", "blancos"]
    assert tree[0]["serving_temp"] == "14–18 °C" and len(tree[0]["children"]) == 4
    facets = client.get("/catalog/wine-facets").json()
    assert facets["body"][2] == {
        "code": "full",
        "name_es": "Con cuerpo",
        "name_en": "Full-bodied",
        "name_fr": "Corsé",
        "name_nl": "Vol",
        "name_de": "Kräftig",
    }
    assert facets["price_ranges"] == ["€", "€€", "€€€", "€€€€"]


def test_every_plan_sees_the_shop_cellar_and_nobody_writes_it(client, seeded, make_user):
    h, _ = make_user()  # free plan
    wine = _shop_wine(
        seeded, "Viña Tondonia Reserva", "tinto-cuerpo-crianza", winery="López de Heredia",
        appellation="D.O.Ca. Rioja", grapes="tempranillo, garnacha", ageing="reserva",
    )  # fmt: skip
    body = client.get("/wines", headers=h).json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["source_name"] == "Vinoselección" and item["source_price"] == 12.5
    assert item["in_stock"] and item["shop_url"] == wine.source_url
    card = client.get(f"/wines/{wine.id}", headers=h).json()
    assert card["category"]["parent"]["name_es"] == "Tintos" and card["checked_at"]
    # The app cannot create, edit or delete wines any more
    assert client.post("/wines", json={"name": "x"}, headers=h).status_code == 405
    assert client.put(f"/wines/{wine.id}", json={"name": "x"}, headers=h).status_code == 405
    assert client.delete(f"/wines/{wine.id}", headers=h).status_code == 405
    assert client.post("/imports/wine", json={"url": SHOP + "x"}, headers=h).status_code in (
        404,
        405,
    )
    assert client.get("/wines").status_code == 401


def test_search_puts_what_can_be_bought_first(client, seeded, make_user):
    h, _ = make_user()
    _shop_wine(seeded, "Albariño Agotado", "blanco-aromatico", in_stock=False)
    _shop_wine(seeded, "Pazo de Señoráns", "blanco-aromatico", grapes="albariño")
    tondonia = _shop_wine(seeded, "Viña Tondonia", "tinto-cuerpo-crianza", ageing="reserva")
    names = [w["name"] for w in client.get("/wines", headers=h).json()["items"]]
    assert names == ["Pazo de Señoráns", "Viña Tondonia", "Albariño Agotado"]
    assert client.get("/wines?in_stock=true", headers=h).json()["total"] == 2
    assert client.get("/wines?q=albariño", headers=h).json()["total"] == 2
    tintos = client.get("/catalog/wine-categories").json()[0]["id"]
    found = client.get(f"/wines?category_id={tintos}&ageing=reserva", headers=h).json()["items"]
    assert [w["id"] for w in found] == [tondonia.id]

    # Favourites are per person
    client.post(f"/wines/{tondonia.id}/favorite", headers=h)
    favs = client.get("/wines?favorites=true", headers=h).json()["items"]
    assert [w["id"] for w in favs] == [tondonia.id] and favs[0]["is_favorite"]
    luis_h, _ = make_user("Luis")
    assert client.get("/wines?favorites=true", headers=luis_h).json()["total"] == 0
    client.delete(f"/wines/{tondonia.id}/favorite", headers=h)
    assert client.get("/wines?favorites=true", headers=h).json()["total"] == 0

    # Por tipos counts what is for sale
    counts = {
        c["category_id"]: c["count"] for c in client.get("/wines/category-counts", headers=h).json()
    }
    assert counts[tintos] == 1 and counts[_wtype(seeded, "blanco-aromatico")] == 1


def test_shop_link_carries_the_agent_code(monkeypatch):
    url = "https://www.vinoseleccion.com/la-vicalanda-reserva-2021"
    assert wine_service.shop_url(url, "") == url
    assert wine_service.shop_url(url, "utm_source=cookinerapp") == url + "?utm_source=cookinerapp"
    assert wine_service.shop_url(url + "?a=1", "?b=2") == url + "?a=1&b=2"


def test_upsert_updates_the_same_page(seeded):
    first = _shop_wine(seeded, "Supernova Reserva", "tinto-cuerpo-crianza", source_price=20)
    again = _shop_wine(seeded, "Supernova Reserva", "tinto-cuerpo-crianza", source_price=18)
    assert first.id == again.id and float(again.source_price) == 18


def test_recipe_wines_and_automatic_suggestion(client, seeded, make_user):
    h, _ = make_user()  # free plan: recommending wines is for everyone now
    stew = marmitako(
        seeded, title="Cocido", category_ids=[_cat(seeded, "cocidos-potajes")], tag_ids=[]
    )
    rid = client.post("/recipes", json=stew, headers=h).json()["id"]
    young = _shop_wine(seeded, "Tinto joven de casa", "tinto-joven")
    _shop_wine(seeded, "Oloroso Don Nuño", "oloroso")
    _shop_wine(seeded, "Oloroso agotado", "oloroso", in_stock=False)
    _shop_wine(seeded, "Albariño", "blanco-aromatico")

    body = client.get(f"/recipes/{rid}/wines", headers=h).json()
    assert body["recommended"] == []
    sug = body["suggestion"]
    assert _cat(seeded, "legumbres") == sug["based_on"]["id"]
    assert [w["wine_category"]["slug"] for w in sug["wine_types"]] == [
        "tinto-joven", "tinto-medio", "oloroso", "amontillado",
    ]  # fmt: skip
    # Shop wines of those types, in the order of the rules; sold-out ones left out
    assert [w["name"] for w in sug["wines"]] == ["Tinto joven de casa", "Oloroso Don Nuño"]
    # ...unless they are the person's favourites, which come first
    oloroso = client.get("/wines?q=agotado", headers=h).json()["items"][0]
    client.post(f"/wines/{oloroso['id']}/favorite", headers=h)
    sug = client.get(f"/recipes/{rid}/wines", headers=h).json()["suggestion"]
    assert sug["wines"][0]["name"] == "Oloroso agotado"

    r = client.post(
        f"/recipes/{rid}/wines", json={"wine_id": young.id, "reason": "El de siempre"}, headers=h
    )
    assert r.status_code == 201 and r.json()["suggestion"] is None
    r = client.post(
        f"/recipes/{rid}/wines", json={"wine_id": young.id, "reason": "Fresco"}, headers=h
    )
    rec = r.json()["recommended"]
    assert len(rec) == 1 and rec[0]["reason"] == "Fresco" and rec[0]["wine"]["shop_url"]
    assert client.post(f"/recipes/{rid}/wines", json={"wine_id": 99999}, headers=h).status_code == (
        404
    )

    assert client.delete(f"/recipes/{rid}/wines/{rec[0]['id']}", headers=h).status_code == 200
    assert client.get(f"/recipes/{rid}/wines", headers=h).json()["suggestion"] is not None
    assert client.get(f"/wines/{young.id}", headers=h).status_code == 200


def test_roles_in_a_shared_notebook(client, seeded, make_user, share):
    ana_h, _ = make_user("Ana")
    luis_h, _ = make_user("Luis")
    eva_h, _ = make_user("Eva")
    nb = share(ana_h, "ana@example.com", luis_h, role="editor")
    share(ana_h, "ana@example.com", eva_h, role="viewer")
    rid = client.post("/recipes", json=marmitako(seeded), headers=ana_h).json()["id"]
    fino = _shop_wine(seeded, "Fino Inocente", "fino-manzanilla")

    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": fino.id}, headers=luis_h)
    link = r.json()["recommended"][0]
    assert link["added_by"] == "Luis"
    # A viewer cannot recommend; the owner can remove the editor's recommendation
    r = client.post(f"/recipes/{rid}/wines", json={"wine_id": fino.id}, headers=eva_h)
    assert r.status_code == 404
    assert client.delete(f"/recipes/{rid}/wines/{link['id']}", headers=ana_h).status_code == 200

    # "Recomendado para": only the recipes of the notebook asked for
    client.post(
        f"/recipes/{rid}/wines", json={"wine_id": fino.id, "reason": "Con el atún"}, headers=ana_h
    )
    mine = client.get(f"/wines/{fino.id}/recipes", headers=ana_h).json()
    assert [(x["recipe_id"], x["reason"]) for x in mine] == [(rid, "Con el atún")]
    assert client.get(f"/wines/{fino.id}/recipes", headers=luis_h).json() == []  # his own
    shared = client.get(f"/wines/{fino.id}/recipes?notebook_id={nb}", headers=eva_h).json()
    assert [x["recipe_id"] for x in shared] == [rid]
    pepe_h, _ = make_user("Pepe")
    r = client.get(f"/wines/{fino.id}/recipes?notebook_id={nb}", headers=pepe_h)
    assert r.status_code == 404
