# CookinerApp

Recetario compartido por grupos (familias, amigos) con búsqueda por ingredientes, tiempo, cocinero, fuente, estación y época; importación de recetas y vinos desde páginas web conservando el enlace a la fuente original; vídeos de YouTube embebidos y vinos recomendados para cada receta.

- **Backend:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy · Alembic (`backend/`)
- **App móvil:** Expo / React Native, iOS y Android (`mobile/`)
- **Idiomas:** español e inglés
- **Documentación técnica:** `docs/` — la documentación de producto vive fuera del repositorio (carpeta `CookinerApp - Docs`)

## Arrancar en local (backend)

Requisitos: Docker Desktop y git.

1. Clonar el repositorio y entrar en la carpeta.
2. Copiar las variables de entorno: `cp .env.example .env` (los valores por defecto sirven para desarrollo).
3. Arrancar la base de datos y la API: `docker compose up --build`
4. Aplicar las migraciones (en otra terminal): `docker compose exec api alembic upgrade head`
5. Abrir http://localhost:8000/docs — la documentación interactiva de la API. `GET /health` debe responder `{"status": "ok"}`.

Para parar: `docker compose down`. Para borrar también la base de datos: `docker compose down -v`.

## Estructura del repositorio

```
backend/   API FastAPI (app/, tests/, alembic/, scripts/)
mobile/    App Expo / React Native
docs/      Arquitectura, modelo de datos, API y decisiones técnicas
.github/   Comprobaciones automáticas
```

Las normas completas de organización, nombres y commits están en `CookinerApp - Docs/00 - Resumen maestro/CookinerApp - Normas de organización.md`.
