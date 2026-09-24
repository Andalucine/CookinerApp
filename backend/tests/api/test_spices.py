from sqlalchemy import select

from app.models import Ingredient
from tests.api.test_recipes import marmitako


def _id(db, name):
    return db.scalar(select(Ingredient).where(Ingredient.name == name)).id


def test_families_list_and_rules(client, seeded):
    fams = client.get("/spices/families").json()
    assert [f["code"] for f in fams][:2] == ["herbs", "seeds"]
    assert fams[0]["name_es"] == "Hierbas aromáticas" and fams[0]["name_en"] == "Herbs"
    assert sum(f["count"] for f in fams) == 113  # approved catalogue

    herbs = client.get("/spices?family=herbs").json()
    assert all(s["family"] == "herbs" for s in herbs) and len(herbs) == fams[0]["count"]
    # Aliases and English names are searchable
    assert [s["name"] for s in client.get("/spices?q=hierbabuena").json()] == ["menta"]
    assert "comino" in [s["name"] for s in client.get("/spices?q=cumin").json()]

    rules = client.get("/spices/rules").json()
    assert rules[0]["situation_es"] == "Hierba fresca ⇄ seca"


def test_spice_card_and_blends(client, seeded):
    card = client.get(f"/spices/{_id(seeded, 'comino')}").json()
    assert card["has_substitutions"] and not card["is_blend"]
    assert card["substitutions"][1]["substitute_es"] == "Alcaravea"
    assert card["substitutions"][1]["ratio"] == "1 : ½"
    assert card["substitutions"][1]["substitute_id"] == _id(seeded, "alcaravea")
    assert "ras el hanout" in [b["name"] for b in card["used_in_blends"]]

    curry = client.get(f"/spices/{_id(seeded, 'curry en polvo')}").json()
    assert curry["is_blend"] and curry["blend"]["items"][0] == {
        "ingredient_id": _id(seeded, "cúrcuma"), "name": "cúrcuma", "name_en": "turmeric",
        "parts": "2", "is_optional": False,
    }  # fmt: skip
    blends = client.get("/spices/blends").json()
    assert len(blends) == 20

    # Fresh ingredients with substitutions have a card too; others do not
    assert client.get(f"/spices/{_id(seeded, 'ajo')}").json()["family"] is None
    assert client.get("/spices/999999").status_code == 404


def test_recipe_spices_check_my_pantry(client, seeded, make_user):
    h, _ = make_user()
    rid = client.post("/recipes", json=marmitako(seeded), headers=h).json()["id"]
    client.post("/pantry/items", json={"name": "pimentón agridulce"}, headers=h)

    spices = client.get(f"/recipes/{rid}/spices", headers=h).json()
    # Only the ingredients with a card, in recipe order (not bonito, patata or sal)
    assert [s["name"] for s in spices] == ["pimentón dulce", "cebolla"]
    paprika = spices[0]
    assert paprika["in_my_pantry"] is False
    have = [s["substitute_es"] for s in paprika["substitutions"] if s["in_my_pantry"]]
    assert have == ["Pimentón agridulce"]

    # Nobody else can see it
    other_h, _ = make_user("Luis")
    assert client.get(f"/recipes/{rid}/spices", headers=other_h).status_code == 404
