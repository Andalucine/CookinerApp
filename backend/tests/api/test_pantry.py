from tests.api.test_recipes import marmitako


def test_pantry_and_what_can_i_cook(client, seeded, make_user):
    headers, _ = make_user()
    client.post("/recipes", json=marmitako(seeded), headers=headers)
    client.post(
        "/recipes",
        json=marmitako(
            seeded,
            title="Tortilla de patatas",
            ingredients=[
                {"name": "patata"},
                {"name": "huevo"},
                {"name": "cebolla"},
                {"name": "sal"},
            ],
        ),
        headers=headers,
    )
    for name, location in (("patata", "pantry"), ("cebolla", "pantry"), ("Huevo", "fridge")):
        r = client.post("/pantry/items", json={"name": name, "location": location}, headers=headers)
        assert r.status_code == 201, r.text
    # adding the same ingredient again just updates its location
    client.post("/pantry/items", json={"name": "huevo", "location": "pantry"}, headers=headers)
    pantry = client.get("/pantry", headers=headers).json()["items"]
    assert sorted(i["name"] for i in pantry) == ["cebolla", "huevo", "patata"]

    r = client.get("/pantry/what-can-i-cook", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert [c["recipe"]["title"] for c in body["complete"]] == ["Tortilla de patatas"]
    assert body["missing_one"] == []  # marmitako lacks bonito AND pimentón

    client.post("/pantry/items", json={"name": "bonito"}, headers=headers)
    body = client.get("/pantry/what-can-i-cook", headers=headers).json()
    assert [c["recipe"]["title"] for c in body["missing_one"]] == ["Marmitako"]
    assert [m["name"] for m in body["missing_one"][0]["missing"]] == ["pimentón dulce"]

    item_id = next(i["id"] for i in pantry if i["name"] == "patata")
    assert client.delete(f"/pantry/items/{item_id}", headers=headers).status_code == 200
    assert client.delete(f"/pantry/items/{item_id}", headers=headers).status_code == 404
