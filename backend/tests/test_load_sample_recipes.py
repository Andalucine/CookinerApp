from scripts import load_sample_recipes


def test_loads_the_samples_once(client, seeded, make_user, capsys):
    headers, _ = make_user("Beatriz")
    assert load_sample_recipes.main(["beatriz@example.com"], db=seeded) == 0
    recipes = client.get("/recipes", headers=headers).json()
    assert recipes["total"] == 4
    marmitako = next(r for r in recipes["items"] if r["title"].startswith("Marmitako"))
    assert marmitako["primary_category"]["slug"] == "guisos-pescado"
    torrijas = client.get("/recipes?q=torrijas", headers=headers).json()["items"][0]
    full = client.get(f"/recipes/{torrijas['id']}", headers=headers).json()
    assert [o["name_es"] for o in full["occasions"]] == ["Semana Santa"]

    # Running it again adds nothing
    assert load_sample_recipes.main(["beatriz@example.com"], db=seeded) == 0
    assert client.get("/recipes", headers=headers).json()["total"] == 4
    assert "ya estaban" in capsys.readouterr().out


def test_unknown_account(seeded):
    assert load_sample_recipes.main(["nadie@example.com"], db=seeded) == 1
    assert load_sample_recipes.main([], db=seeded) == 1
