"""The one-off script that empties the notebooks' cellars before Vinoselección (session 9)."""

from sqlalchemy import select

from app.models import Favorite, RecipeWine, Wine
from scripts.switch_to_vinoseleccion import switch
from tests.api.test_recipes import marmitako
from tests.api.test_wines import _shop_wine


def test_switch_deletes_every_wine_and_its_links_and_can_run_again(client, seeded, make_user):
    h, _ = make_user()
    rid = client.post("/recipes", json=marmitako(seeded), headers=h).json()["id"]
    wine = _shop_wine(seeded, "Viña Tondonia", "tinto-cuerpo-crianza")
    client.post(f"/recipes/{rid}/wines", json={"wine_id": wine.id}, headers=h)
    client.post(f"/wines/{wine.id}/favorite", headers=h)
    client.post(f"/recipes/{rid}/favorite", headers=h)  # recipe favourites are kept

    lines = []
    assert switch(seeded.get_bind(), echo=lines.append) == 1
    seeded.expire_all()
    assert seeded.scalar(select(Wine)) is None and seeded.scalar(select(RecipeWine)) is None
    favourites = seeded.scalars(select(Favorite)).all()
    assert [f.recipe_id for f in favourites] == [rid]
    assert "Columnas quitadas: ninguna" in lines
    assert switch(seeded.get_bind(), echo=lines.append) == 0
