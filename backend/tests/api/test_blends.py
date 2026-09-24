"""Blends of a notebook (session 8): own blends, versions of catalogue blends, roles."""

from sqlalchemy import select

from app.models import Ingredient


def _id(db, name):
    return db.scalar(select(Ingredient.id).where(Ingredient.name == name))


CURRY = {
    "name": "Curry en polvo",
    "note": "Mi curry, con más comino",
    "items": [
        {"name": "cúrcuma", "parts": "2"},
        {"name": "comino", "parts": "2"},
        {"name": "canela", "parts": "¼", "is_optional": True},
    ],
}


def test_own_version_of_a_catalogue_blend(client, seeded, make_user):
    h, ana = make_user("Ana")  # free plan: blends are for everyone
    curry_id = _id(seeded, "curry en polvo")

    # Without a token the card is the catalogue's
    card = client.get(f"/spices/{curry_id}").json()
    assert card["is_blend"] and card["notebook_blend_id"] is None
    catalogue_items = len(card["blend"]["items"])

    r = client.post("/blends", json=CURRY, headers=h)
    assert r.status_code == 201, r.text
    mine = r.json()
    assert mine["ingredient_id"] == curry_id and mine["notebook_id"] == ana["notebook_id"]
    assert [i["name"] for i in mine["items"]] == ["cúrcuma", "comino", "canela"]
    assert mine["items"][2]["is_optional"] is True
    assert mine["added_by"] is None  # the owner herself

    # With the token, the card shows my version first and keeps the catalogue's
    card = client.get(f"/spices/{curry_id}", headers=h).json()
    assert card["is_own_version"] and card["notebook_blend_id"] == mine["notebook_blend_id"]
    assert len(card["blend"]["items"]) == 3 and card["blend"]["note_es"] == CURRY["note"]
    assert len(card["catalog_blend"]["items"]) == catalogue_items
    # …and the list marks it
    blends = client.get("/spices?family=blends", headers=h).json()
    row = next(b for b in blends if b["id"] == curry_id)
    assert row["is_own_version"] and row["notebook_blend_id"] == mine["notebook_blend_id"]

    # A second version with the same name is refused; editing is the way
    assert client.post("/blends", json=CURRY, headers=h).status_code == 409
    r = client.put(
        f"/blends/{mine['notebook_blend_id']}",
        json={**CURRY, "items": [{"name": "cúrcuma", "parts": "3"}]},
        headers=h,
    )
    assert r.status_code == 200 and [i["parts"] for i in r.json()["items"]] == ["3"]

    # Deleting my version goes back to the catalogue's
    assert client.delete(f"/blends/{mine['notebook_blend_id']}", headers=h).status_code == 200
    card = client.get(f"/spices/{curry_id}", headers=h).json()
    assert not card["is_own_version"] and card["catalog_blend"] is None
    assert len(card["blend"]["items"]) == catalogue_items


def test_new_blend_of_the_notebook(client, seeded, make_user):
    h, _ = make_user("Ana")
    body = {
        "name": "Mezcla de la abuela",
        "items": [{"name": "pimentón dulce", "parts": "2"}, {"name": "orégano", "parts": "1"}],
    }
    r = client.post("/blends", json=body, headers=h)
    assert r.status_code == 201, r.text
    blend = r.json()
    assert blend["name"] == "mezcla de la abuela" and blend["id"] is None

    # It shows in Mezclas and in searches, only with my token, and has a card
    names = [b["name"] for b in client.get("/spices?family=blends", headers=h).json()]
    assert "mezcla de la abuela" in names
    assert "mezcla de la abuela" not in [
        b["name"] for b in client.get("/spices?family=blends").json()
    ]
    found = client.get("/spices?q=abuela", headers=h).json()
    assert [b["name"] for b in found] == ["mezcla de la abuela"] and found[0]["is_blend"]
    card = client.get(f"/spices/{blend['ingredient_id']}", headers=h).json()
    assert card["is_blend"] and not card["is_own_version"] and card["catalog_blend"] is None
    assert client.get(f"/spices/{blend['ingredient_id']}").status_code == 404  # nobody else's

    # The blend cannot contain itself; the list of the notebook's blends
    bad = {**body, "items": [{"name": "Mezcla de la abuela", "parts": "1"}]}
    assert (
        client.put(f"/blends/{blend['notebook_blend_id']}", json=bad, headers=h).status_code == 422
    )
    assert [b["name"] for b in client.get("/blends", headers=h).json()] == ["mezcla de la abuela"]


def test_shared_notebook_roles(client, seeded, make_user, share):
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")
    nb = share(ana_h, "ana@example.com", luis_h, role="viewer")
    body = {"name": "Adobo de Luis", "notebook_id": nb, "items": [{"name": "comino", "parts": "1"}]}

    # A viewer sees the notebook's blends but cannot add
    assert client.get(f"/blends?notebook_id={nb}", headers=luis_h).status_code == 200
    assert client.post("/blends", json=body, headers=luis_h).status_code == 404

    # An editor adds, and the blend is marked with his name for the owner
    client.patch(f"/notebooks/mine/access/{luis['id']}", json={"role": "editor"}, headers=ana_h)
    r = client.post("/blends", json=body, headers=luis_h)
    assert r.status_code == 201, r.text
    blend = r.json()
    assert blend["added_by"] == "Luis"
    row = next(
        b
        for b in client.get("/spices?family=blends", headers=ana_h).json()
        if b["id"] == blend["ingredient_id"]
    )
    assert row["added_by"] == "Luis"

    # Eva, with no access, sees nothing of it
    eva_h, _ = make_user("Eva")
    assert client.get(f"/blends?notebook_id={nb}", headers=eva_h).status_code == 404
    assert (
        client.put(f"/blends/{blend['notebook_blend_id']}", json=body, headers=eva_h).status_code
        == 404
    )

    # The owner may delete what Luis created; Luis may delete his own too, but not Ana's
    ana_blend = client.post(
        "/blends",
        json={"name": "Adobo de Ana", "items": [{"name": "comino", "parts": "1"}]},
        headers=ana_h,
    ).json()
    assert (
        client.delete(f"/blends/{ana_blend['notebook_blend_id']}", headers=luis_h).status_code
        == 403
    )
    assert client.delete(f"/blends/{blend['notebook_blend_id']}", headers=ana_h).status_code == 200
