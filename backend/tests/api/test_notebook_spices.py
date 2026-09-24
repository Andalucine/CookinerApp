"""Spices of a notebook and its own substitute lists (session 8)."""

from sqlalchemy import select

from app.models import Ingredient
from tests.api.test_recipes import marmitako


def _id(db, name):
    return db.scalar(select(Ingredient.id).where(Ingredient.name == name))


def test_own_spice_in_its_family(client, seeded, make_user):
    h, ana = make_user("Ana")
    body = {"name": "Pimentón de mi pueblo", "family": "paprikas", "aliases": "Pimentón casero"}
    r = client.post("/notebook-spices", json=body, headers=h)
    assert r.status_code == 201, r.text
    spice = r.json()
    assert spice["name"] == "pimentón de mi pueblo" and spice["aliases"] == "pimentón casero"

    # In its family (with my token), counted, searchable by alias, with a card; not for others
    fam = next(
        f for f in client.get("/spices/families", headers=h).json() if f["code"] == "paprikas"
    )
    assert fam["count"] == 6  # 5 in the catalogue + mine
    rows = client.get("/spices?family=paprikas", headers=h).json()
    mine = next(s for s in rows if s["id"] == spice["ingredient_id"])
    assert mine["notebook_spice_id"] == spice["id"] and not mine["has_substitutions"]
    assert [s["name"] for s in client.get("/spices?q=casero", headers=h).json()] == [spice["name"]]
    assert client.get("/spices?q=casero").json() == []
    card = client.get(f"/spices/{spice['ingredient_id']}", headers=h).json()
    assert card["family"] == "paprikas" and card["notebook_spice_id"] == spice["id"]
    assert client.get(f"/spices/{spice['ingredient_id']}").status_code == 404

    # A catalogue name is refused; editing moves it to another family
    bad = {"name": "comino", "family": "seeds"}
    assert client.post("/notebook-spices", json=bad, headers=h).status_code == 409
    r = client.put(
        f"/notebook-spices/{spice['id']}", json={**body, "family": "salts_seasonings"}, headers=h
    )
    assert r.status_code == 200 and r.json()["family"] == "salts_seasonings"
    assert [s["name"] for s in client.get("/notebook-spices", headers=h).json()] == [spice["name"]]

    assert client.delete(f"/notebook-spices/{spice['id']}", headers=h).status_code == 200
    assert client.get(f"/spices/{spice['ingredient_id']}", headers=h).status_code == 404


def test_own_substitutes_replace_the_catalogue_list(client, seeded, make_user):
    h, ana = make_user("Ana")
    nigella = _id(seeded, "nigella")
    comino = _id(seeded, "comino")
    assert client.get(f"/spices/{nigella}").json()["substitutions"] == []
    catalogue_comino = client.get(f"/spices/{comino}").json()["substitutions"]
    assert len(catalogue_comino) >= 2

    # Nigella had none: now my notebook has a list, linked to the catalogue when it is one name
    items = [
        {"substitute": "Comino", "ratio": "1 : 1", "note": "Más suave"},
        {"substitute": "Sésamo negro + orégano", "ratio": "mitad y mitad"},
    ]
    r = client.put(f"/notebook-spices/{nigella}/substitutions", json={"items": items}, headers=h)
    assert r.status_code == 200, r.text
    subs = r.json()
    assert subs[0]["substitute_id"] == comino and subs[1]["substitute_id"] is None
    card = client.get(f"/spices/{nigella}", headers=h).json()
    assert card["has_own_substitutions"] and card["has_substitutions"]
    assert [s["substitute_es"] for s in card["substitutions"]] == [
        "Comino",
        "Sésamo negro + orégano",
    ]
    assert client.get(f"/spices/{nigella}").json()["substitutions"] == []  # catalogue untouched
    row = next(
        s for s in client.get("/spices?family=seeds", headers=h).json() if s["id"] == nigella
    )
    assert row["has_substitutions"]

    # Comino: my list replaces the catalogue's for me; a spice cannot be its own substitute
    r = client.put(
        f"/notebook-spices/{comino}/substitutions",
        json={"items": [{"substitute": "Alcaravea", "ratio": "1 : ½"}]},
        headers=h,
    )
    assert r.status_code == 200
    assert len(client.get(f"/spices/{comino}", headers=h).json()["substitutions"]) == 1
    assert len(client.get(f"/spices/{comino}").json()["substitutions"]) == len(catalogue_comino)
    bad = {"items": [{"substitute": "comino"}]}
    assert (
        client.put(f"/notebook-spices/{comino}/substitutions", json=bad, headers=h).status_code
        == 422
    )

    # Back to the catalogue's; a second time there is nothing to remove
    assert client.delete(f"/notebook-spices/{comino}/substitutions", headers=h).status_code == 200
    card = client.get(f"/spices/{comino}", headers=h).json()
    assert not card["has_own_substitutions"] and len(card["substitutions"]) == len(catalogue_comino)
    assert client.delete(f"/notebook-spices/{comino}/substitutions", headers=h).status_code == 404

    # The spices of a recipe use the notebook's list
    recipe = marmitako(seeded)
    recipe["ingredients"].append(
        {"name": "nigella", "quantity": 1, "unit": "cdta", "raw_text": None}
    )
    rid = client.post("/recipes", json=recipe, headers=h).json()["id"]
    spices = client.get(f"/recipes/{rid}/spices", headers=h).json()
    nig = next(s for s in spices if s["ingredient_id"] == nigella)
    assert [s["substitute_es"] for s in nig["substitutions"]][0] == "Comino"


def test_shared_notebook_roles_for_spices(client, seeded, make_user, share):
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")
    nb = share(ana_h, "ana@example.com", luis_h, role="viewer")
    body = {"name": "Hierba de Luis", "family": "herbs", "notebook_id": nb}
    assert client.post("/notebook-spices", json=body, headers=luis_h).status_code == 404
    client.patch(f"/notebooks/mine/access/{luis['id']}", json={"role": "editor"}, headers=ana_h)
    r = client.post("/notebook-spices", json=body, headers=luis_h)
    assert r.status_code == 201 and r.json()["added_by"] == "Luis"
    spice = r.json()
    nigella = _id(seeded, "nigella")
    r = client.put(
        f"/notebook-spices/{nigella}/substitutions",
        json={"items": [{"substitute": "Comino"}], "notebook_id": nb},
        headers=luis_h,
    )
    assert r.status_code == 200
    card = client.get(f"/spices/{nigella}?notebook_id={nb}", headers=ana_h).json()
    assert card["has_own_substitutions"] and card["substitutions_added_by"] == "Luis"
    # Only the owner or Luis delete his spice; Eva sees nothing
    eva_h, _ = make_user("Eva")
    assert client.delete(f"/notebook-spices/{spice['id']}", headers=eva_h).status_code == 404
    assert client.delete(f"/notebook-spices/{spice['id']}", headers=ana_h).status_code == 200
