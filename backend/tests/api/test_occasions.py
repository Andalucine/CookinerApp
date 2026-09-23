from tests.api.test_recipes import marmitako


def test_own_occasions_listed_after_preloaded(client, seeded, make_user):
    h, user = make_user()
    preloaded = client.get("/catalog/occasions").json()
    r = client.post("/occasions", json={"name": "  Romería   del Rocío "}, headers=h)
    assert r.status_code == 201, r.text
    own = r.json()
    assert own["name_es"] == own["name_en"] == "Romería del Rocío"
    assert own["notebook_id"] == user["notebook_id"] and not own["is_preloaded"]
    client.post("/occasions", json={"name": "Cumpleaños de la abuela"}, headers=h)

    listed = client.get("/occasions", headers=h).json()
    assert [o["id"] for o in listed[: len(preloaded)]] == [o["id"] for o in preloaded]
    assert [o["name_es"] for o in listed[len(preloaded) :]] == [
        "Cumpleaños de la abuela", "Romería del Rocío",
    ]  # fmt: skip
    # Other notebooks do not see it, and the public catalogue stays the same
    other_h, _ = make_user("Luis")
    assert len(client.get("/occasions", headers=other_h).json()) == len(preloaded)
    assert len(client.get("/catalog/occasions").json()) == len(preloaded)


def test_duplicates_rename_delete_and_preloaded_locked(client, seeded, make_user):
    h, _ = make_user()
    navidad = next(o for o in client.get("/catalog/occasions").json() if o["name_es"] == "Navidad")
    assert client.post("/occasions", json={"name": "navidad"}, headers=h).status_code == 409
    oid = client.post("/occasions", json={"name": "Matanza"}, headers=h).json()["id"]
    assert client.post("/occasions", json={"name": "MATANZA"}, headers=h).status_code == 409

    r = client.put(f"/occasions/{oid}", json={"name": "Matanza del cerdo"}, headers=h)
    assert r.json()["name_es"] == "Matanza del cerdo"
    assert (
        client.put(f"/occasions/{navidad['id']}", json={"name": "x"}, headers=h).status_code == 403
    )
    assert client.delete(f"/occasions/{navidad['id']}", headers=h).status_code == 403

    # Used in a recipe and searchable; deleting it keeps the recipe
    rid = client.post("/recipes", json=marmitako(seeded, occasion_ids=[oid]), headers=h).json()[
        "id"
    ]
    assert client.get(f"/recipes?occasion_id={oid}", headers=h).json()["total"] == 1
    assert client.delete(f"/occasions/{oid}", headers=h).status_code == 200
    assert client.get(f"/recipes/{rid}", headers=h).json()["occasions"] == []


def test_occasions_roles_and_other_notebooks(client, seeded, make_user, share):
    ana_h, _ = make_user("Ana")
    luis_h, _ = make_user("Luis")
    eva_h, _ = make_user("Eva")
    nb = share(ana_h, "ana@example.com", luis_h, role="editor")
    share(ana_h, "ana@example.com", eva_h, role="viewer")
    ana_occ = client.post("/occasions", json={"name": "Feria de abril"}, headers=ana_h).json()

    # Editor adds one to Ana's notebook; it is marked as his; he cannot delete Ana's
    r = client.post("/occasions", json={"name": "Carnaval", "notebook_id": nb}, headers=luis_h)
    assert r.status_code == 201 and r.json()["added_by"] == "Luis"
    luis_occ = r.json()
    assert client.delete(f"/occasions/{ana_occ['id']}", headers=luis_h).status_code == 403
    assert client.delete(f"/occasions/{luis_occ['id']}", headers=luis_h).status_code == 200

    # Viewer sees them but cannot add or change
    names = [o["name_es"] for o in client.get(f"/occasions?notebook_id={nb}", headers=eva_h).json()]
    assert "Feria de abril" in names
    r = client.post("/occasions", json={"name": "x", "notebook_id": nb}, headers=eva_h)
    assert r.status_code == 404
    assert (
        client.put(f"/occasions/{ana_occ['id']}", json={"name": "x"}, headers=eva_h).status_code
        == 404
    )

    # An own occasion only works inside its notebook
    r = client.post("/recipes", json=marmitako(seeded, occasion_ids=[ana_occ["id"]]), headers=eva_h)
    assert r.status_code == 422
    r = client.post(
        "/recipes", json=marmitako(seeded, occasion_ids=[ana_occ["id"]], notebook_id=nb),
        headers=luis_h,
    )  # fmt: skip
    assert r.status_code == 201
