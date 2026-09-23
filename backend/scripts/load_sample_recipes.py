"""Load four sample recipes into someone's notebook, to try and show the app locally.

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.load_sample_recipes beatriz@correo.es

Marmitako, torrijas, gazpacho and lentejas, with categories, seasons and an occasion, so the
recipe screens have something to show. Recipes already in the notebook (same title) are
skipped, so it can be run again. Development only; needs the catalogues loaded first.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Category, Occasion, Recipe, Season, User
from app.schemas.recipe import RecipeIn, RecipeIngredientIn
from app.services import recipe as recipe_service


def _ing(name: str, quantity: float | None = None, unit: str | None = None) -> RecipeIngredientIn:
    return RecipeIngredientIn(name=name, quantity=quantity, unit=unit)


# (recipe fields, category slugs, season codes, occasion names in Spanish)
SAMPLES: list[tuple[dict, list[str], list[str], list[str]]] = [
    (
        {
            "title": "Marmitako de la abuela Carmen",
            "description": "Guiso marinero de bonito con patatas, el de los otoños en casa.",
            "instructions": (
                "Pica la cebolla y el pimiento verde y póchalos en aceite a fuego suave.\n"
                "Añade el tomate rallado, la carne de pimiento choricero y el pimentón.\n"
                "Echa las patatas cascadas, cubre con agua y cuece 20 minutos.\n"
                "Apaga el fuego, añade el bonito en tacos con sal y deja reposar 5 minutos."
            ),
            "prep_time_minutes": 45,
            "servings": 4,
            "cook_name": "abuela Carmen",
            "source_type": "family",
            "ingredients": [
                _ing("bonito", 600, "g"),
                _ing("patata", 4),
                _ing("cebolla", 1),
                _ing("pimiento verde", 1),
                _ing("pimiento choricero", 2),
                _ing("tomate", 1),
                _ing("pimentón de la vera", 1, "cdta"),
                _ing("aceite de oliva"),
                _ing("sal"),
            ],
        },
        ["guisos-pescado"],
        ["autumn"],
        [],
    ),
    (
        {
            "title": "Torrijas",
            "description": (
                "Pan del día anterior empapado en leche aromatizada, frito y rebozado en azúcar."
            ),
            "instructions": (
                "Calienta la leche con la canela, la piel de limón y la mitad del azúcar.\n"
                "Corta el pan en rebanadas gruesas y empápalas bien en la leche templada.\n"
                "Pásalas por huevo batido y fríelas en aceite caliente hasta que se doren.\n"
                "Escúrrelas y rebózalas en azúcar con canela molida."
            ),
            "prep_time_minutes": 40,
            "servings": 6,
            "cook_name": "abuela Carmen",
            "source_type": "family",
            "ingredients": [
                _ing("pan", 1, "barra"),
                _ing("leche", 1, "l"),
                _ing("azúcar", 150, "g"),
                _ing("canela en rama", 1),
                _ing("limón", 1),
                _ing("huevo", 3),
                _ing("aceite de oliva"),
            ],
        },
        ["dulces-fritos"],
        ["spring"],
        ["Semana Santa"],
    ),
    (
        {
            "title": "Gazpacho andaluz",
            "description": "Sopa fría de tomate para los días de calor.",
            "instructions": (
                "Trocea los tomates, el pepino, el pimiento y el ajo.\n"
                "Tritura todo con el pan remojado, el vinagre y la sal.\n"
                "Añade el aceite poco a poco sin dejar de triturar.\n"
                "Cuela si lo quieres fino y enfría al menos una hora."
            ),
            "prep_time_minutes": 20,
            "servings": 4,
            "source_type": "own",
            "ingredients": [
                _ing("tomate", 1, "kg"),
                _ing("pepino", 1),
                _ing("pimiento verde", 1),
                _ing("ajo", 1, "diente"),
                _ing("pan", 50, "g"),
                _ing("vinagre de jerez", 2, "cda"),
                _ing("aceite de oliva", 80, "ml"),
                _ing("sal"),
            ],
        },
        ["sopas-frias"],
        ["summer"],
        [],
    ),
    (
        {
            "title": "Lentejas con chorizo",
            "description": "Lentejas de cuchara para el invierno.",
            "instructions": (
                "Pon las lentejas en agua fría con la zanahoria, la cebolla, el ajo y el laurel.\n"
                "Cuando rompa a hervir, añade el chorizo en rodajas y la patata troceada.\n"
                "Añade el pimentón y cuece a fuego suave unos 50 minutos.\n"
                "Rectifica de sal y deja reposar antes de servir."
            ),
            "prep_time_minutes": 75,
            "servings": 4,
            "source_type": "own",
            "ingredients": [
                _ing("lenteja pardina", 300, "g"),
                _ing("chorizo", 1),
                _ing("zanahoria", 2),
                _ing("patata", 1),
                _ing("cebolla", 1),
                _ing("ajo", 2, "diente"),
                _ing("pimentón dulce", 1, "cdta"),
                _ing("laurel", 1, "hoja"),
                _ing("sal"),
            ],
        },
        ["guisos-legumbres"],
        ["winter"],
        [],
    ),
]


class UnknownUser(Exception):
    pass


def _ids(db: Session, model, column, values: list[str]) -> list[int]:
    return [db.scalar(select(model.id).where(column == v)) for v in values]


def load(db: Session, email: str) -> list[str]:
    """Add the samples missing from the person's notebook; return the titles added."""
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise UnknownUser
    notebook = user.notebook
    existing = set(db.scalars(select(Recipe.title).where(Recipe.notebook_id == notebook.id)))
    added = []
    for fields, categories, seasons, occasions in SAMPLES:
        if fields["title"] in existing:
            continue
        data = RecipeIn(
            **fields,
            category_ids=_ids(db, Category, Category.slug, categories),
            season_ids=_ids(db, Season, Season.code, seasons),
            occasion_ids=[
                db.scalar(
                    select(Occasion.id).where(
                        Occasion.name_es == name, Occasion.notebook_id.is_(None)
                    )
                )
                for name in occasions
            ],
        )
        recipe_service.create(db, user, notebook.id, user, data)
        added.append(fields["title"])
    return added


def main(args: list[str], db: Session | None = None) -> int:
    if len(args) != 1:
        print(__doc__)
        return 1
    session = db or SessionLocal()
    try:
        added = load(session, args[0])
    except UnknownUser:
        print(f"✗ No hay ninguna cuenta con el correo {args[0]}")
        return 1
    except recipe_service.RecipeLimitReached:
        print("✗ El cuaderno ha llegado al máximo de recetas de su plan")
        return 1
    finally:
        if db is None:
            session.close()
    if added:
        print("✓ Recetas añadidas: " + ", ".join(added))
    else:
        print("✓ Las recetas de ejemplo ya estaban en el cuaderno")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
