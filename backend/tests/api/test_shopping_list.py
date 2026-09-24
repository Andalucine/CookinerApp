from tests.api.test_recipes import marmitako


def test_shopping_list_sections_and_from_recipe(client, seeded, make_user):
    headers, _ = make_user()
    rid = client.post("/recipes", json=marmitako(seeded), headers=headers).json()["id"]
    client.post("/pantry/items", json={"name": "patata"}, headers=headers)

    r = client.post(f"/shopping-list/from-recipe/{rid}", headers=headers)
    assert r.status_code == 200
    # patata is in the pantry, sal is a staple → bonito, pimentón dulce, cebolla
    assert sorted(i["text"] for i in r.json()) == ["bonito", "cebolla", "pimentón dulce"]
    # running it again does not duplicate what is already pending
    assert client.post(f"/shopping-list/from-recipe/{rid}", headers=headers).json() == []

    r = client.post(
        "/shopping-list/items", json={"text": "Manzanas", "quantity": "1 kg"}, headers=headers
    )
    assert r.status_code == 201
    client.post("/shopping-list/items", json={"text": "leche"}, headers=headers)

    body = client.get("/shopping-list", headers=headers).json()
    assert body["total"] == 5 and body["pending"] == 5
    by_section = {s["code"]: [i["text"] for i in s["items"]] for s in body["sections"]}
    assert by_section["spices"] == ["pimentón dulce"]
    # the everyday catalogue (session 9) knows plurals: "Manzanas" → manzana
    assert sorted(by_section["produce"]) == ["Manzanas", "cebolla"]
    assert by_section["fish"] == ["bonito"] and by_section["dairy"] == ["leche"]
    assert list(by_section) == ["produce", "fish", "dairy", "spices"]  # supermarket order

    item = body["sections"][0]["items"][0]
    assert (
        client.post(f"/shopping-list/items/{item['id']}/check", headers=headers).status_code == 200
    )
    body = client.get("/shopping-list", headers=headers).json()
    assert body["pending"] == 4
    r = client.delete("/shopping-list/checked", headers=headers)
    assert "1" in r.json()["message"]
    assert client.get("/shopping-list", headers=headers).json()["total"] == 4


def test_move_to_another_section_is_remembered_by_the_notebook(client, seeded, make_user):
    headers, _ = make_user()
    other_h, _ = make_user("Luis")
    r = client.post("/shopping-list/items", json={"text": "Tofu ahumado"}, headers=headers)
    tofu = r.json()
    sections = client.get("/shopping-list", headers=headers).json()["sections"]
    assert [s["code"] for s in sections] == ["other"]  # unknown → Otros

    r = client.patch(
        f"/shopping-list/items/{tofu['id']}", json={"section_code": "dairy"}, headers=headers
    )
    assert r.status_code == 200
    assert [
        s["code"] for s in client.get("/shopping-list", headers=headers).json()["sections"]
    ] == ["dairy"]
    # next time it goes straight to Lácteos in this notebook, not in someone else's
    client.post("/shopping-list/items", json={"text": "tofu ahumado"}, headers=headers)
    body = client.get("/shopping-list", headers=headers).json()
    assert [(s["code"], len(s["items"])) for s in body["sections"]] == [("dairy", 2)]
    client.post("/shopping-list/items", json={"text": "tofu ahumado"}, headers=other_h)
    other = client.get("/shopping-list", headers=other_h).json()["sections"]
    assert [s["code"] for s in other] == ["other"]

    bad = {"section_code": "moon"}
    assert (
        client.patch(f"/shopping-list/items/{tofu['id']}", json=bad, headers=headers).status_code
        == 404
    )
    ok = {"section_code": "produce"}
    assert (
        client.patch(f"/shopping-list/items/{tofu['id']}", json=ok, headers=other_h).status_code
        == 404
    )


def test_clear_bought_can_note_it_in_the_pantry(client, seeded, make_user):
    headers, _ = make_user()
    ids = {}
    for text in ("2 kg de patatas", "leche", "helado", "papel de horno"):
        name = "patatas" if text.startswith("2") else text
        r = client.post(
            "/shopping-list/items", json={"text": text, "ingredient_name": name}, headers=headers
        )
        ids[text] = r.json()["id"]
    for text in ("2 kg de patatas", "leche", "helado"):
        client.post(f"/shopping-list/items/{ids[text]}/check", headers=headers)

    r = client.delete("/shopping-list/checked?to_pantry=true", headers=headers)
    assert r.status_code == 200 and "3" in r.json()["message"]
    pantry = {
        i["name"]: i["location"] for i in client.get("/pantry", headers=headers).json()["items"]
    }
    assert pantry == {"patata": "fridge", "leche": "fridge", "helado": "freezer"}
    left = client.get("/shopping-list", headers=headers).json()
    assert left["total"] == 1  # papel de horno was not bought yet

    # without to_pantry, nothing goes to the pantry
    client.post(f"/shopping-list/items/{ids['papel de horno']}/check", headers=headers)
    client.delete("/shopping-list/checked", headers=headers)
    assert len(client.get("/pantry", headers=headers).json()["items"]) == 3


def test_missing_preview_and_ticked_ingredients(client, seeded, make_user):
    headers, _ = make_user()
    rid = client.post("/recipes", json=marmitako(seeded), headers=headers).json()["id"]
    client.post("/pantry/items", json={"name": "patata"}, headers=headers)
    client.post("/shopping-list/items", json={"text": "cebolla"}, headers=headers)

    r = client.get(f"/shopping-list/from-recipe/{rid}", headers=headers)
    assert r.status_code == 200
    status = {row["name"]: row["status"] for row in r.json()}
    assert status == {
        "bonito": "missing", "patata": "in_pantry", "pimentón dulce": "missing",
        "cebolla": "pending", "sal": "staple",
    }  # fmt: skip
    assert next(row for row in r.json() if row["name"] == "patata")["quantity"] == "4 patatas"

    # tick only bonito and patata (patata is in the pantry, but the person wants more)
    ids = {row["name"]: row["ingredient_id"] for row in r.json()}
    r = client.post(
        f"/shopping-list/from-recipe/{rid}",
        json={"ingredient_ids": [ids["bonito"], ids["patata"], ids["cebolla"]]},
        headers=headers,
    )
    assert r.status_code == 200
    assert sorted(i["text"] for i in r.json()) == ["bonito", "patata"]  # cebolla was pending
