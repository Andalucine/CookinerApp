"""The development script that adds missing tables and columns without touching data."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from scripts.sync_dev_schema import sync


def test_sync_creates_missing_tables_and_columns_and_keeps_rows():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # An old database: the ingredients table without the "va bien con" columns, with a row
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE ingredients (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, "
                "name_en VARCHAR(100), aliases VARCHAR(300), is_spice BOOLEAN NOT NULL, "
                "spice_family VARCHAR(30), shopping_section_id INTEGER)"
            )
        )
        c.execute(text("INSERT INTO ingredients (name, is_spice) VALUES ('comino', 1)"))

    created, added = sync(engine)
    assert "ingredients" not in created and "notebook_spice_pairings" in created
    assert {"weekly_menus", "menu_slots"} <= set(created)  # session 9
    assert {"ingredients.pairs_with_es", "ingredients.pairs_with_en"} <= set(added)
    columns = {c["name"] for c in inspect(engine).get_columns("ingredients")}
    assert "pairs_with_es" in columns
    with engine.connect() as c:
        assert c.execute(text("SELECT name FROM ingredients")).scalar() == "comino"

    # Running it again changes nothing
    assert sync(engine) == ([], [])
