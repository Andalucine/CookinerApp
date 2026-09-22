from sqlalchemy import select

from app.models import Category, Ingredient, NotebookAccess, Occasion, RecipeContribution, Tag


def _cat(db, slug):
    return db.scalar(select(Category).where(Category.slug == slug)).id


def _tag(db, kind, code):
    return db.scalar(select(Tag).where(Tag.kind == kind, Tag.code == code)).id


def marmitako(db, **overrides):
    body = {
        "title": "Marmitako",
        "description": "Guiso de bonito con patatas",
        "instructions": "Sofreír, añadir patatas, caldo y el bonito al final.",
        "prep_time_minutes": 45,
        "servings": 4,
        "cook_name": "la abuela Carmen",
        "source_type": "family",
        "ingredients": [
            {"name": "Bonito", "quantity": 500, "unit": "g"},
            {"name": "patata", "quantity": 4, "unit": "unidad", "raw_text": "4 patatas"},
            {"name": "Pimentón dulce", "quantity": 1, "unit": "cdta"},
            {"name": "cebolla", "quantity": 1},
            {"name": "sal"},
        ],
        "category_ids": [_cat(db, "guisos-pescado"), _cat(db, "pescado-azul")],
        "tag_ids": [_tag(db, "method", "stewed"), _tag(db, "course", "main")],
    }
    body.update(overrides)
    return body


def test_create_recipe_links_catalogue_and_creates_new_ingredients(client, seeded, make_user):
    headers, user = make_user()
    before = seeded.scalar(select(Ingredient).where(Ingredient.name == "bonito"))
    assert before is None

    r = client.post("/recipes", json=marmitako(seeded), headers=headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["notebook_id"] == user["notebook_id"]
    assert body["time_label"] == "medium"
    assert body["primary_category"]["slug"] == "guisos-pescado"
    assert [c["slug"] for c in body["categories"]] == ["guisos-pescado", "pescado-azul"]
    assert [i["name"] for i in body["ingredients"]] == [
        "bonito", "patata", "pimentón dulce", "cebolla", "sal"
    ]  # fmt: skip
    assert body["added_by"] is None  # the owner wrote it
    assert body["author"]["display_name"] == "Ana"
    # "Pimentón dulce" matched the spice from the catalogue instead of creating a duplicate
    pimenton = seeded.scalar(select(Ingredient).where(Ingredient.name == "pimentón dulce"))
    assert pimenton.is_spice
    # new ingredient created in the global catalogue, in section "other"
    bonito = seeded.scalar(select(Ingredient).where(Ingredient.name == "bonito"))
    assert bonito.shopping_section.code == "other"


def test_web_recipe_requires_source_url(client, seeded, make_user):
    headers, _ = make_user()
    r = client.post("/recipes", json=marmitako(seeded, source_type="web"), headers=headers)
    assert r.status_code == 422
    r = client.post(
        "/recipes",
        json=marmitako(seeded, source_type="web", source_url="https://ejemplo.com/marmitako"),
        headers=headers,
    )
    assert r.status_code == 201


def test_unknown_category_is_rejected(client, seeded, make_user):
    headers, _ = make_user()
    r = client.post("/recipes", json=marmitako(seeded, category_ids=[99999]), headers=headers)
    assert r.status_code == 422


def test_search_filters(client, seeded, make_user):
    headers, _ = make_user()
    semana_santa = seeded.scalar(select(Occasion).where(Occasion.name_es == "Semana Santa")).id
    client.post("/recipes", json=marmitako(seeded), headers=headers)
    client.post(
        "/recipes",
        json=marmitako(
            seeded,
            title="Torrijas",
            description="Las de Semana Santa",
            prep_time_minutes=25,
            cook_name=None,
            source_type="own",
            ingredients=[{"name": "pan"}, {"name": "leche"}, {"name": "huevo"}, {"name": "canela"}],
            category_ids=[_cat(seeded, "dulces-fritos")],
            tag_ids=[_tag(seeded, "method", "fried")],
            occasion_ids=[semana_santa],
        ),
        headers=headers,
    )

    def search(**params):
        r = client.get("/recipes", params=params, headers=headers)
        assert r.status_code == 200, r.text
        return [i["title"] for i in r.json()["items"]]

    assert sorted(search()) == ["Marmitako", "Torrijas"]
    assert search(ingredients="patata") == ["Marmitako"]
    assert search(ingredients="patata,bonito") == ["Marmitako"]
    assert search(ingredients="patata,leche") == []
    assert search(ingredients="Pimentón") == ["Marmitako"]  # any case, partial
    assert search(time="quick") == ["Torrijas"]
    assert search(max_minutes=30) == ["Torrijas"]
    assert search(cook="abuela") == ["Marmitako"]
    assert search(cook="ana") == ["Marmitako", "Torrijas"] or search(cook="ana") == [
        "Torrijas", "Marmitako"
    ]  # fmt: skip
    assert search(source_type="family") == ["Marmitako"]
    assert search(occasion_id=semana_santa) == ["Torrijas"]
    assert search(category_id=_cat(seeded, "pescados")) == ["Marmitako"]  # parent includes children
    assert search(category_id=_cat(seeded, "dulce")) == ["Torrijas"]  # branch includes everything
    assert search(tag_ids=str(_tag(seeded, "method", "fried"))) == ["Torrijas"]
    assert search(q="bonito") == ["Marmitako"]  # description too
    assert search(favorites=True) == []


def test_favorites(client, seeded, make_user):
    headers, _ = make_user()
    rid = client.post("/recipes", json=marmitako(seeded), headers=headers).json()["id"]
    assert client.post(f"/recipes/{rid}/favorite", headers=headers).status_code == 200
    assert client.post(f"/recipes/{rid}/favorite", headers=headers).status_code == 200  # idempotent
    r = client.get("/recipes", params={"favorites": True}, headers=headers)
    assert [i["id"] for i in r.json()["items"]] == [rid]
    assert client.get(f"/recipes/{rid}", headers=headers).json()["is_favorite"] is True
    client.delete(f"/recipes/{rid}/favorite", headers=headers)
    assert client.get(f"/recipes/{rid}", headers=headers).json()["is_favorite"] is False


def test_free_plan_limit(client, seeded, make_user):
    headers, user = make_user()
    assert user["max_recipes"] == 15
    for i in range(15):
        r = client.post("/recipes", json=marmitako(seeded, title=f"Receta {i}"), headers=headers)
        assert r.status_code == 201
    r = client.post("/recipes", json=marmitako(seeded, title="Una más"), headers=headers)
    assert r.status_code == 403
    assert "plan" in r.json()["detail"]


def _grant(db, notebook_id, user_id, role):
    db.add(NotebookAccess(notebook_id=notebook_id, user_id=user_id, role=role))
    db.commit()


def test_sharing_roles(client, seeded, make_user):
    ana_h, ana = make_user("Ana")
    luis_h, luis = make_user("Luis")
    pepa_h, pepa = make_user("Pepa")
    rid = client.post("/recipes", json=marmitako(seeded), headers=ana_h).json()["id"]

    # Nobody else sees Ana's recipe until she shares
    assert client.get(f"/recipes/{rid}", headers=luis_h).status_code == 404
    r = client.get("/recipes", params={"notebook_id": ana["notebook_id"]}, headers=luis_h)
    assert r.status_code == 404

    _grant(seeded, ana["notebook_id"], luis["id"], "viewer")
    _grant(seeded, ana["notebook_id"], pepa["id"], "editor")

    # Viewer: reads, cannot edit or add
    assert client.get(f"/recipes/{rid}", headers=luis_h).status_code == 200
    r = client.put(f"/recipes/{rid}", json=marmitako(seeded, title="X"), headers=luis_h)
    assert r.status_code == 404
    r = client.post(
        "/recipes", json={**marmitako(seeded), "notebook_id": ana["notebook_id"]}, headers=luis_h
    )
    assert r.status_code == 403
    r = client.get("/recipes", params={"all_notebooks": True}, headers=luis_h)
    assert [i["id"] for i in r.json()["items"]] == [rid]

    # Editor: adds a recipe to Ana's notebook → marked "(añadido por Pepa)"
    r = client.post(
        "/recipes",
        json={**marmitako(seeded, title="Pestiños"), "notebook_id": ana["notebook_id"]},
        headers=pepa_h,
    )
    assert r.status_code == 201
    assert r.json()["added_by"] == "Pepa"
    assert r.json()["notebook_id"] == ana["notebook_id"]

    # Editor edits Ana's recipe → contribution recorded; the owner editing does not
    r = client.put(
        f"/recipes/{rid}",
        json=marmitako(seeded, instructions="Ahora con un chorrito de txakoli."),
        headers=pepa_h,
    )
    assert r.status_code == 200
    contribs = seeded.scalars(select(RecipeContribution)).all()
    assert [(c.user_id, c.field) for c in contribs] == [(pepa["id"], "instructions")]
    client.put(f"/recipes/{rid}", json=marmitako(seeded, title="Marmitako de casa"), headers=ana_h)
    assert len(seeded.scalars(select(RecipeContribution)).all()) == 1

    # Editor cannot delete the owner's recipe; the owner can
    assert client.delete(f"/recipes/{rid}", headers=pepa_h).status_code == 403
    assert client.delete(f"/recipes/{rid}", headers=ana_h).status_code == 200
    assert client.get(f"/recipes/{rid}", headers=ana_h).status_code == 404
