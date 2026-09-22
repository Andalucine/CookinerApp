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
    assert by_section["produce"] == ["cebolla"]
    assert sorted(by_section["other"]) == ["Manzanas", "bonito", "leche"]  # unknown → Otros
    assert list(by_section) == ["produce", "spices", "other"]  # supermarket order

    item = body["sections"][0]["items"][0]
    assert (
        client.post(f"/shopping-list/items/{item['id']}/check", headers=headers).status_code == 200
    )
    body = client.get("/shopping-list", headers=headers).json()
    assert body["pending"] == 4
    r = client.delete("/shopping-list/checked", headers=headers)
    assert "1" in r.json()["message"]
    assert client.get("/shopping-list", headers=headers).json()["total"] == 4
