"""Menú semanal (session 9): a draft with the notebook's recipes and the rules of the bible."""

from tests.api.test_recipes import _cat, _tag, marmitako

WEEK = "2026-09-28"  # a Monday, autumn


def _recipes(client, seeded, headers):
    """Two mains of different categories, one breakfast, one summer-only main."""
    ids = {}
    ids["marmitako"] = client.post("/recipes", json=marmitako(seeded), headers=headers).json()["id"]
    ids["lentejas"] = client.post(
        "/recipes",
        json=marmitako(
            seeded,
            title="Lentejas",
            ingredients=[{"name": "lentejas"}, {"name": "chorizo"}, {"name": "sal"}],
            category_ids=[_cat(seeded, "guisos-legumbres")],
            tag_ids=[_tag(seeded, "course", "main")],
        ),
        headers=headers,
    ).json()["id"]
    ids["tostadas"] = client.post(
        "/recipes",
        json=marmitako(
            seeded,
            title="Tostadas con tomate",
            ingredients=[{"name": "pan"}, {"name": "tomate"}, {"name": "aceite de oliva"}],
            category_ids=[_cat(seeded, "bocadillos-montaditos")],
            tag_ids=[_tag(seeded, "course", "breakfast")],
        ),
        headers=headers,
    ).json()["id"]
    summer = client.get("/catalog/seasons").json()
    summer_id = next(s["id"] for s in summer if s["code"] == "summer")
    ids["gazpacho"] = client.post(
        "/recipes",
        json=marmitako(
            seeded,
            title="Gazpacho",
            ingredients=[{"name": "tomate"}, {"name": "pepino"}],
            season_ids=[summer_id],
            tag_ids=[_tag(seeded, "course", "main")],
        ),
        headers=headers,
    ).json()["id"]
    return ids


def test_check_and_draft_follow_the_rules(client, seeded, make_user):
    h, _ = make_user()
    ids = _recipes(client, seeded, h)

    r = client.get(f"/menus/check?week_start={WEEK}", headers=h)
    assert r.status_code == 200
    assert r.json() == {
        "week_start": WEEK, "season": "autumn", "total_recipes": 4,
        "breakfast_recipes": 1, "main_recipes": 3,
    }  # fmt: skip
    assert client.get(f"/menus?week_start={WEEK}", headers=h).status_code == 404

    r = client.post(
        "/menus/draft",
        json={"week_start": "2026-09-30", "meals": ["breakfast", "lunch", "dinner"]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    menu = r.json()
    assert menu["week_start"] == WEEK and menu["meals"] == ["breakfast", "lunch", "dinner"]
    assert len(menu["slots"]) == 21
    breakfasts = [s for s in menu["slots"] if s["meal"] == "breakfast"]
    assert all(s["recipe"]["id"] == ids["tostadas"] for s in breakfasts)
    mains = [s for s in menu["slots"] if s["meal"] != "breakfast"]
    # gazpacho is summer-only: never in an autumn week; the two mains alternate
    assert {s["recipe"]["id"] for s in mains} == {ids["marmitako"], ids["lentejas"]}
    for day in range(7):
        lunch, dinner = [s["recipe"]["id"] for s in mains if s["day"] == day]
        assert lunch != dinner
    assert "repeated" in menu["notices"] and "no_breakfast_recipes" not in menu["notices"]

    # the week is found by any of its days; a new draft replaces it
    r = client.get("/menus?week_start=2026-10-04", headers=h)
    assert r.status_code == 200 and r.json()["id"] == menu["id"]
    r = client.post("/menus/draft", json={"week_start": WEEK, "meals": ["lunch"]}, headers=h)
    assert r.status_code == 201 and len(r.json()["slots"]) == 7
    assert client.get(f"/menus?week_start={WEEK}", headers=h).json()["id"] == r.json()["id"]


def test_wants_pantry_and_notices(client, seeded, make_user):
    h, _ = make_user()
    ids = _recipes(client, seeded, h)
    # "me apetecen lentejas": every lunch is lentejas; the rest is said in the notices
    r = client.post(
        "/menus/draft",
        json={"week_start": WEEK, "meals": ["lunch"], "wants": "lentejas"},
        headers=h,
    )
    slots = r.json()["slots"]
    # the wanted recipe comes first, but a recipe is not repeated while others are unused
    assert slots[0]["recipe"]["id"] == ids["lentejas"]
    assert sum(1 for s in slots if s["recipe"]["id"] == ids["lentejas"]) >= 3
    assert "filled_with_rest" in r.json()["notices"]  # one lentejas recipe cannot fill a week
    # a food nobody has: the draft fills with the rest and says so
    r = client.post(
        "/menus/draft", json={"week_start": WEEK, "meals": ["lunch"], "wants": "caviar"}, headers=h
    )
    assert "filled_with_rest" in r.json()["notices"]
    # breakfast asked in a notebook without breakfast recipes: empty slots + notice
    other_h, _ = make_user("Luis")
    client.post("/recipes", json=marmitako(seeded), headers=other_h)
    r = client.post(
        "/menus/draft", json={"week_start": WEEK, "meals": ["breakfast", "lunch"]}, headers=other_h
    )
    assert "no_breakfast_recipes" in r.json()["notices"]
    assert all(s["recipe"] is None for s in r.json()["slots"] if s["meal"] == "breakfast")
    assert all(s["recipe"] is not None for s in r.json()["slots"] if s["meal"] == "lunch")


def test_edit_slots_another_and_shopping(client, seeded, make_user):
    h, _ = make_user()
    ids = _recipes(client, seeded, h)
    menu = client.post(
        "/menus/draft", json={"week_start": WEEK, "meals": ["lunch", "dinner"]}, headers=h
    ).json()
    first = menu["slots"][0]
    # write by hand
    r = client.put(
        f"/menus/{menu['id']}/slots/{first['id']}",
        json={"recipe_id": None, "note": "Cenamos fuera"},
        headers=h,
    )
    assert r.status_code == 200 and r.json()["recipe"] is None
    assert r.json()["note"] == "Cenamos fuera"
    # choose a recipe (the summer one is allowed by hand)
    r = client.put(
        f"/menus/{menu['id']}/slots/{first['id']}", json={"recipe_id": ids["gazpacho"]}, headers=h
    )
    assert r.json()["recipe"]["title"] == "Gazpacho" and r.json()["note"] is None
    # another proposal: a different recipe from the mains
    second = menu["slots"][1]
    before = second["recipe"]["id"]
    r = client.post(f"/menus/{menu['id']}/slots/{second['id']}/another", headers=h)
    assert r.status_code == 200 and r.json()["recipe"]["id"] != before
    # someone else's recipe cannot be put in my menu
    other_h, _ = make_user("Luis")
    foreign = client.post("/recipes", json=marmitako(seeded), headers=other_h).json()["id"]
    r = client.put(
        f"/menus/{menu['id']}/slots/{first['id']}", json={"recipe_id": foreign}, headers=h
    )
    assert r.status_code == 404
    assert client.get(f"/menus/{menu['id']}/shopping", headers=other_h).status_code == 405
    assert client.post(f"/menus/{menu['id']}/shopping", headers=other_h).status_code == 404

    # the shopping list for the whole week: every ingredient not at home, once
    client.post("/pantry/items", json={"name": "patata"}, headers=h)
    r = client.post(f"/menus/{menu['id']}/shopping", headers=h)
    assert r.status_code == 200
    texts = sorted(i["text"] for i in r.json()["added"])
    assert "patata" not in texts and "sal" not in texts
    assert "lenteja" in texts or "lentejas" in texts
    assert len(texts) == len(set(texts))  # no duplicates across the 14 meals
    assert r.json()["recipes"] >= 2
    # again: nothing new (already pending)
    assert client.post(f"/menus/{menu['id']}/shopping", headers=h).json()["added"] == []

    assert client.delete(f"/menus/{menu['id']}", headers=h).status_code == 200
    assert client.get(f"/menus?week_start={WEEK}", headers=h).status_code == 404
