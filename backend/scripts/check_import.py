"""Check how well the importer reads real recipe pages (the test sites of the bible).

Run from `backend/` (in Docker: docker compose exec api python -m scripts.check_import URL...):

    python -m scripts.check_import https://www.recetasderechupete.com/receta-de-lentejas-caseras-con-chorizo/939/

For each page it prints what it found, so we know which sites need special handling.
Nothing is saved.
"""

import sys

from app.services import importer


def _how(p: importer.RecipePreview) -> str:
    if not p.complete:
        return "NO (solo título y foto)"
    return "sí, leídos del texto de la página (revisar)" if p.from_text else "sí"


def summary(url: str) -> str:
    try:
        final_url, html = importer.fetch_html(url)
        p = importer.read_recipe(html, final_url)
    except importer.InvalidUrl:
        return f"✗ {url}\n  Dirección no válida"
    except importer.FetchFailed:
        return f"✗ {url}\n  No se pudo abrir la página"
    except importer.NoRecipeFound:
        return f"✗ {url}\n  Sin receta ni título"
    tick = "✓" if p.complete and not p.from_text else "△" if p.complete else "✗"
    lines = [
        f"{tick} {url}",
        f"  Título: {p.title}",
        f"  Fuente: {p.source_name} · Autor: {p.cook_name or '—'}",
        f"  Datos de receta: {_how(p)}",
        f"  Ingredientes: {len(p.ingredients)} · Pasos: {'sí' if p.instructions else 'no'}"
        f" · Tiempo: {p.prep_time_minutes or '—'} min · Raciones: {p.servings or '—'}",
        f"  Foto: {'sí' if p.image_url else 'no'} · Vídeo YouTube: {p.youtube_url or 'no'}",
    ]
    for line in p.ingredients[:3]:
        lines.append(f"    · {line.raw_text}  →  {line.quantity} | {line.unit} | {line.name}")
    return "\n".join(lines)


def main(urls: list[str]) -> int:
    if not urls:
        print(__doc__)
        return 1
    for url in urls:
        print(summary(url), end="\n\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
