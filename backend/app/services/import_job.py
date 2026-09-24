"""Import jobs: read a web page into an editable preview, then save it as a recipe.

Every attempt is recorded in `import_jobs` (history and debugging). The page is read again
never: the preview travels to the app and comes back edited with the save request.
"""

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.i18n import LANGUAGES
from app.models import ImportJob, Ingredient, Notebook, User
from app.models.user import PLANS_WITH_IMPORT
from app.schemas.recipe import RecipeIn, RecipeIngredientIn
from app.services import importer
from app.services import recipe as recipe_service

KIND_RECIPE = "recipe"
STATUS_PENDING, STATUS_OK, STATUS_ERROR = "pending", "ok", "error"


class ImportNotInPlan(Exception):
    pass


class ImportJobNotFound(Exception):
    pass


class AlreadySaved(Exception):
    pass


def require_import(notebook: Notebook) -> None:
    """Importing follows the plan of the notebook OWNER (decision, session 5)."""
    if notebook.owner.plan not in PLANS_WITH_IMPORT:
        raise ImportNotInPlan


def _catalog_name(db: Session, name: str) -> str | None:
    norm = recipe_service.normalise_name(name)
    hit = db.scalar(
        select(Ingredient.name).where(
            or_(
                Ingredient.name == norm,
                Ingredient.aliases == norm,
                Ingredient.aliases.ilike(f"{norm},%"),
                Ingredient.aliases.ilike(f"%, {norm}"),
                Ingredient.aliases.ilike(f"%, {norm},%"),
            )
        )
    )
    return hit


def match_ingredient(db: Session, name: str) -> str:
    """'Ajo picados' → 'ajo'; 'Tomates' → 'tomate' when the catalogue has it.

    Tries the whole name and then drops words from the end, each time also in singular.
    With no match it keeps the name as written (lowercase); the user can fix it.
    """
    words = recipe_service.normalise_name(name).split()
    for size in range(len(words), 0, -1):
        candidate = " ".join(words[:size])
        variants = [candidate]
        if candidate.endswith("es"):
            variants.append(candidate[:-2])
        if candidate.endswith("s"):
            variants.append(candidate[:-1])
        for variant in variants:
            hit = _catalog_name(db, variant)
            if hit:
                return hit
    return " ".join(words)


def _warnings(preview: importer.RecipePreview) -> list[str]:
    if not preview.complete:
        return ["no_recipe_data"]
    missing = ["read_from_text"] if preview.from_text else []
    if not preview.ingredients:
        missing.append("no_ingredients")
    if not preview.instructions:
        missing.append("no_instructions")
    if preview.prep_time_minutes is None:
        missing.append("no_time")
    return missing


def start(
    db: Session, user: User, notebook: Notebook, url: str
) -> tuple[ImportJob, list[str], RecipeIn]:
    """Download and read the page. Returns (job, warnings, RecipeIn) or raises after
    recording the error in the job."""
    job = ImportJob(user_id=user.id, notebook_id=notebook.id, kind=KIND_RECIPE, url=url.strip())
    db.add(job)
    db.commit()
    try:
        final_url, html = importer.fetch_html(job.url)
        preview = importer.read_recipe(html, final_url)
    except (importer.InvalidUrl, importer.FetchFailed, importer.NoRecipeFound) as exc:
        job.status, job.error_message = STATUS_ERROR, type(exc).__name__
        job.finished_at = datetime.now(UTC)
        db.commit()
        raise
    job.status = STATUS_PENDING  # read; waiting for the user to confirm
    db.commit()
    draft = RecipeIn(
        title=preview.title,
        description=preview.description,
        instructions=preview.instructions,
        prep_time_minutes=preview.prep_time_minutes,
        servings=preview.servings,
        cook_name=preview.cook_name,
        source_type="web",
        source_name=(preview.source_name or "")[:200] or None,
        source_url=preview.source_url[:1000],
        youtube_url=preview.youtube_url,
        image_url=(preview.image_url or "")[:1000] or None,
        language=user.language if user.language in LANGUAGES else "es",
        ingredients=[
            RecipeIngredientIn(
                name=match_ingredient(db, line.name),
                quantity=line.quantity,
                unit=line.unit,
                raw_text=line.raw_text,
            )
            for line in preview.ingredients
        ],
    )
    return job, _warnings(preview), draft


def get(db: Session, user: User, job_id: int) -> ImportJob:
    job = db.get(ImportJob, job_id)
    if job is None or job.user_id != user.id:
        raise ImportJobNotFound
    return job


def save(db: Session, user: User, job: ImportJob, notebook: Notebook, data: RecipeIn):
    """Create the recipe from the (edited) preview and link it to the job."""
    if job.recipe_id is not None:
        raise AlreadySaved
    recipe = recipe_service.create(db, user, notebook.id, notebook.owner, data)
    job.recipe_id, job.status, job.finished_at = recipe.id, STATUS_OK, datetime.now(UTC)
    db.commit()
    return recipe


def history(db: Session, user: User, limit: int = 20) -> list[ImportJob]:
    return list(
        db.scalars(
            select(ImportJob)
            .where(ImportJob.user_id == user.id)
            .order_by(ImportJob.created_at.desc(), ImportJob.id.desc())
            .limit(limit)
        )
    )
