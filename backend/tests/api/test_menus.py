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
    # the three mains are all used before any repeats, and the summer-only gazpacho is used
    # rather than repeating a plate (with a notice)
    first_three = [s["recipe"]["id"] for s in mains[:3]]
    assert sorted(first_three) == sorted([ids["marmitako"], ids["lentejas"], ids["gazpacho"]])
    # a recipe repeats at most once: 3 recipes → 6 plates, the other 8 stay empty
    filled = [s for s in mains if s["recipe"]]
    assert len(filled) == 6 and all(s["recipe"] is None for s in mains[6:])
    counts = {}
    for s in filled:
        counts[s["recipe"]["id"]] = counts.get(s["recipe"]["id"], 0) + 1
    assert set(counts.values()) == {2}
    for day in range(3):
        lunch, dinner = [s["recipe"]["id"] for s in filled if s["day"] == day]
        assert lunch != dinner
    assert {"repeated", "season_ignored", "not_enough_recipes"} <= set(menu["notices"])
    assert "no_breakfast_recipes" not in menu["notices"]

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
    assert sum(1 for s in slots if s["recipe"] and s["recipe"]["id"] == ids["lentejas"]) == 2
    assert "filled_with_rest" in r.json()["notices"]  # one lentejas recipe cannot fill a week
    # a food found through the category name ("guisos de legumbres")
    r = client.post(
        "/menus/draft",
        json={"week_start": WEEK, "meals": ["lunch"], "wants": "legumbres"},
        headers=h,
    )
    assert r.json()["slots"][0]["recipe"]["id"] == ids["lentejas"]
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
    lunches = [s for s in r.json()["slots"] if s["meal"] == "lunch"]
    assert sum(1 for s in lunches if s["recipe"]) == 2  # one recipe, used twice at most


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
    assert client.get(f"/menus/{menu['id']}/shopping", headers=other_h).status_code == 404
    assert client.post(f"/menus/{menu['id']}/shopping", headers=other_h).status_code == 404

    # the shopping list for the whole week: every ingredient not at home, once
    client.post("/pantry/items", json={"name": "patata"}, headers=h)
    preview = client.get(f"/menus/{menu['id']}/shopping", headers=h).json()
    by_name = {row["name"]: row for row in preview}
    assert by_name["patata"]["status"] == "in_pantry" and by_name["sal"]["status"] == "staple"
    assert len(by_name["tomate"]["recipes"]) >= 1  # gazpacho (put by hand) uses it
    assert len(preview) == len(by_name)  # each ingredient once, whatever the number of meals
    r = client.post(f"/menus/{menu['id']}/shopping", headers=h)
    assert r.status_code == 200
    texts = sorted(i["text"] for i in r.json()["added"])
    assert "patata" not in texts and "sal" not in texts
    assert "lenteja" in texts or "lentejas" in texts
    assert len(texts) == len(set(texts))  # no duplicates across the 14 meals
    assert r.json()["recipes"] >= 2
    # again: nothing new (already pending)
    assert client.post(f"/menus/{menu['id']}/shopping", headers=h).json()["added"] == []
    # the ticked ones only: patata (in the pantry, but asked for)
    r = client.post(
        f"/menus/{menu['id']}/shopping",
        json={"ingredient_ids": [by_name["patata"]["ingredient_id"]]},
        headers=h,
    )
    assert [i["text"] for i in r.json()["added"]] == ["patata"]

    assert client.delete(f"/menus/{menu['id']}", headers=h).status_code == 200
    assert client.get(f"/menus?week_start={WEEK}", headers=h).status_code == 404


def test_only_main_plates_and_light_dinners(client, seeded, make_user):
    """Desserts, tapas and sauces never come out as a lunch or a dinner; a soup goes to
    dinner and a stew to lunch when both are there (session 9, after Beatriz's test)."""
    h, _ = make_user()
    for title, slug, course in (
        ("Torrijas", "dulces-fritos", "dessert"),
        ("Croquetas", "frituras", "appetiser"),
        ("Alioli", "salsas-frias", None),
        ("Cocido", "cocidos-potajes", "main"),
        ("Crema de calabacín", "cremas-pures", "light-dinner"),
    ):
        client.post(
            "/recipes",
            json=marmitako(
                seeded,
                title=title,
                ingredients=[{"name": title.lower()}],
                category_ids=[_cat(seeded, slug)],
                tag_ids=[_tag(seeded, "course", course)] if course else [],
                prep_time_minutes=60 if title == "Cocido" else 20,
            ),
            headers=h,
        )
    r = client.post(
        "/menus/draft", json={"week_start": WEEK, "meals": ["lunch", "dinner"]}, headers=h
    )
    slots = r.json()["slots"]
    titles = {s["recipe"]["title"] for s in slots if s["recipe"]}
    assert titles == {"Cocido", "Crema de calabacín"}
    assert slots[0]["meal"] == "lunch" and slots[0]["recipe"]["title"] == "Cocido"
    assert slots[1]["meal"] == "dinner" and slots[1]["recipe"]["title"] == "Crema de calabacín"
    # "Otra propuesta" respects the cap: with both recipes used twice, nothing else is offered
    assert "not_enough_recipes" in r.json()["notices"]
