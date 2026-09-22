# 0002 — FastAPI + PostgreSQL en el backend, Expo en la app

**Fecha:** sesión 1 (septiembre de 2026), registrada el 2026-09-22

## Contexto
Hace falta una API con búsqueda por varios criterios, importación de contenido web y usuarios por grupos, y una app nativa iOS/Android sencilla.

## Decisión
- Backend en **Python 3.12 + FastAPI**, base de datos **PostgreSQL 16**, ORM **SQLAlchemy 2**, migraciones con **Alembic**.
- App móvil con **Expo / React Native** (una sola base de código para iOS y Android).
- Alojamiento en un servicio gestionado (**Railway o Fly.io**), no en un VPS propio.
- Español e inglés desde el primer día (`i18n/` en backend y app).

## Alternativas descartadas
- Django: más pesado para una API JSON sencilla.
- Web progresiva (PWA) en lugar de app nativa: peor experiencia para usuarios con capacitación digital básica (instalación, notificaciones).
- SQLite: no vale para varios grupos accediendo a la vez desde un servidor.

## Consecuencias
- Docker Compose para tener PostgreSQL en local sin instalarlo.
- Python es el lenguaje habitual de la autora, lo que facilita el mantenimiento.
