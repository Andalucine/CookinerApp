"""Importar: read a recipe from a web page, show an editable preview, save it on confirm.

Two steps so that nothing is saved without the user seeing it first:
1. POST /imports/recipe {url} → preview (not saved) + job id.
2. POST /imports/{job_id}/save {recipe} → the recipe, with its link to the source.
Importing follows the plan of the notebook owner, like wines (403 on a free notebook).
"""

from fastapi import APIRouter, HTTPException, status

from app.api.recipes import to_out
from app.core.deps import CurrentUser, DbSession, Lang
from app.i18n import t
from app.models import Notebook
from app.schemas.import_job import (
    ImportJobOut,
    RecipeImportPreview,
    RecipeImportRequest,
    WineImportPreview,
    WineImportRequest,
)
from app.schemas.recipe import RecipeIn, RecipeOut
from app.services import import_job as import_service
from app.services import importer, permissions, wine_importer
from app.services import recipe as recipe_service
from app.services import wine as wine_service

router = APIRouter(prefix="/imports", tags=["imports"])


def _notebook(db, user, lang, notebook_id: int | None) -> Notebook:
    try:
        notebook = permissions.resolve_notebook(db, user, notebook_id, edit=True)
    except (permissions.NotebookNotFound, permissions.Forbidden):
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("notebook_not_found", lang)) from None
    try:
        import_service.require_import(notebook)
    except import_service.ImportNotInPlan:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("import_not_in_plan", lang)) from None
    return notebook


@router.post("/recipe", response_model=RecipeImportPreview)
def import_recipe(
    body: RecipeImportRequest, db: DbSession, user: CurrentUser, lang: Lang
) -> RecipeImportPreview:
    """Read the recipe of a web page. Nothing is saved yet: the answer is the preview.

    `warnings` lists what the page did not have: no_recipe_data (only title and photo),
    no_ingredients, no_instructions, no_time.
    """
    notebook = _notebook(db, user, lang, body.notebook_id)
    try:
        job, warnings, draft = import_service.start(db, user, notebook, body.url)
    except importer.InvalidUrl:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("import_invalid_url", lang)
        ) from None
    except importer.FetchFailed:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, t("import_fetch_failed", lang)) from None
    except importer.NoRecipeFound:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("import_no_recipe", lang)
        ) from None
    return RecipeImportPreview(
        job_id=job.id, notebook_id=notebook.id, complete="no_recipe_data" not in warnings,
        warnings=warnings, recipe=draft,
    )  # fmt: skip


@router.post("/wine", response_model=WineImportPreview)
def import_wine(
    body: WineImportRequest, db: DbSession, user: CurrentUser, lang: Lang
) -> WineImportPreview:
    """Read a wine from a shop or winery page (session 8). Nothing is saved: the answer is the
    preview, which the app sends to POST /wines when the person confirms."""
    notebook = _notebook(db, user, lang, body.notebook_id)
    try:
        wine_service.require_wines(notebook)
    except wine_service.WinesNotInPlan:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("wines_not_in_plan", lang)) from None
    try:
        final_url, html = wine_importer.fetch_html(body.url)
    except importer.InvalidUrl:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("import_invalid_url", lang)
        ) from None
    except importer.FetchFailed:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, t("import_fetch_failed", lang)) from None
    preview = wine_importer.read_wine(html, final_url)
    wine = wine_service.from_preview(db, preview, final_url, lang)
    return WineImportPreview(
        notebook_id=notebook.id,
        complete="no_product_data" not in preview.warnings,
        warnings=preview.warnings,
        wine=wine,
    )


@router.post("/{job_id}/save", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def save_import(
    job_id: int, body: RecipeIn, db: DbSession, user: CurrentUser, lang: Lang
) -> RecipeOut:
    """Save the (edited) preview as a recipe in the notebook chosen when importing.
    The link to the source is required (source_type web + source_url)."""
    try:
        job = import_service.get(db, user, job_id)
    except import_service.ImportJobNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("import_not_found", lang)) from None
    notebook = _notebook(db, user, lang, job.notebook_id)
    if body.source_type != "web" or not body.source_url:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, t("invalid_reference", lang))
    try:
        recipe = import_service.save(db, user, job, notebook, body)
    except import_service.AlreadySaved:
        raise HTTPException(status.HTTP_409_CONFLICT, t("import_already_saved", lang)) from None
    except recipe_service.RecipeLimitReached:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("recipe_limit_reached", lang)) from None
    except recipe_service.UnknownReference:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, t("invalid_reference", lang)
        ) from None
    return to_out(recipe, set(), permissions.require_edit(db, user, notebook))


@router.get("", response_model=list[ImportJobOut])
def import_history(db: DbSession, user: CurrentUser) -> list[ImportJobOut]:
    """My last 20 import attempts, newest first."""
    return [
        ImportJobOut.model_validate(j, from_attributes=True)
        for j in import_service.history(db, user)
    ]
