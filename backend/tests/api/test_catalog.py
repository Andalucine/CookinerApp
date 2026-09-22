def test_category_tree_has_three_branches(client, seeded):
    r = client.get("/catalog/categories")
    assert r.status_code == 200
    roots = r.json()
    assert [c["slug"] for c in roots] == ["salado", "dulce", "bebidas"]
    pescados = next(c for c in roots[0]["children"] if c["slug"] == "pescados")
    assert pescados["level"] == 2
    assert len(pescados["children"]) == 9
    assert pescados["children"][0]["examples_es"].startswith("merluza")


def test_tags_by_kind_and_sections_in_order(client, seeded):
    r = client.get("/catalog/tags", params={"kind": "diet"})
    assert [t["code"] for t in r.json()] == [
        "vegetarian", "vegan", "gluten-free", "lactose-free", "nut-free", "egg-free", "low-salt"
    ]  # fmt: skip
    r = client.get("/catalog/shopping-sections")
    codes = [s["code"] for s in r.json()]
    assert codes[0] == "produce" and codes[-1] == "other" and len(codes) == 13


def test_ingredient_autocomplete_matches_aliases(client, seeded):
    r = client.get("/catalog/ingredients", params={"q": "hierbabuena"})
    assert [i["name"] for i in r.json()] == ["menta"]
    r = client.get("/catalog/ingredients", params={"q": "pimentón"})
    names = [i["name"] for i in r.json()]
    assert "pimentón dulce" in names and "pimentón de la vera" in names
