# CookinerApp

Cuaderno de cocina personal (recetas, vinos, especias, notas y despensa) que se puede compartir con lectores y editores, con búsqueda por ingredientes, tiempo, cocinero, fuente, estación y época; importación de recetas y vinos desde páginas web conservando el enlace a la fuente original; vídeos de YouTube embebidos y vinos recomendados para cada receta.

- **Backend:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy · Alembic (`backend/`)
- **App móvil:** Expo / React Native, iOS y Android (`mobile/`)
- **Idiomas:** español e inglés
- **Documentación técnica:** `docs/` — la documentación de producto vive fuera del repositorio (carpeta `CookinerApp - Docs`)

## Arrancar en local (backend)

Requisitos: Docker Desktop y git.

1. Clonar el repositorio y entrar en la carpeta.
2. Copiar las variables de entorno: `cp .env.example .env` (los valores por defecto sirven para desarrollo).
3. Arrancar la base de datos y la API: `docker compose up --build`
4. Crear las tablas y cargar los catálogos (en otra terminal): `docker compose exec api alembic upgrade head` y después `docker compose exec api python -m scripts.seed_catalogs` (estaciones, épocas, categorías, etiquetas, especias, vinos, secciones de compra; se puede repetir sin duplicar). Si tenías la base de datos de la sesión 2, antes: `docker compose down -v`.
5. Abrir http://localhost:8000/docs — la documentación interactiva de la API. `GET /health` debe responder `{"status": "ok"}`.

Para parar: `docker compose down`. Para borrar también la base de datos: `docker compose down -v`.

## Arrancar la app móvil

Requisitos: Node.js 20 o posterior, y la app **Expo Go** en el móvil (misma wifi que el ordenador). Con la API en marcha:

1. `cd mobile` y `npm install` (la primera vez).
2. `npx expo start` y escanear el código QR con la cámara del iPhone (o desde Expo Go en Android).

Detalles en `mobile/LEEME.md`.

## Estructura del repositorio

```
backend/   API FastAPI (app/, tests/, alembic/, scripts/)
mobile/    App Expo / React Native
docs/      Arquitectura, modelo de datos, API y decisiones técnicas
.github/   Comprobaciones automáticas
```

Las normas completas de organización, nombres y commits están en `CookinerApp - Docs/00 - Resumen maestro/CookinerApp - Normas de organización.md`.
