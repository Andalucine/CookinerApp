"""The script that shortens the titles of the recipes imported before (session 9)."""

from sqlalchemy import select

from app.models import Recipe
from scripts import retitle_imported
from tests.api.test_recipes import marmitako


def test_only_web_recipes_with_a_long_headline_change(client, seeded, make_user):
    h, user = make_user()
    long = "Tom Kha Gai, la sopa tailandesa de pollo y coco muy aromática"
    client.post(
        "/recipes",
        json=marmitako(
            seeded, title=long, source_type="web", source_url="https://x.test/1", source_name="X"
        ),
        headers=h,
    )
    client.post("/recipes", json=marmitako(seeded, title="Marmitako, el de mi abuela"), headers=h)

    changed = retitle_imported.retitle(seeded, "ana@example.com", echo=lambda s: 0)
    assert changed == [(long, "Tom Kha Gai")]
    titles = set(
        seeded.scalars(select(Recipe.title).where(Recipe.notebook_id == user["notebook_id"]))
    )
    assert titles == {"Tom Kha Gai", "Marmitako, el de mi abuela"}  # a family recipe is left alone
    assert retitle_imported.retitle(seeded, "ana@example.com", echo=lambda s: 0) == []
