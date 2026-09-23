# Arquitectura

```
┌──────────────────────┐        HTTPS/JSON        ┌──────────────────────┐        ┌────────────┐
│  App móvil (Expo)    │ ───────────────────────▶ │  API FastAPI         │ ─────▶ │ PostgreSQL │
│  iOS / Android       │ ◀─────────────────────── │  backend/app         │ ◀───── │            │
└──────────────────────┘                          └──────────┬───────────┘        └────────────┘
                                                             │
                                                             ▼
                                                  Importadores web (recetas, vinos)
                                                  backend/app/services/
```

## Piezas

- **mobile/** — la app que usan las personas (Expo SDK 57, Expo Router; decisión 0006). Solo habla con la API; no accede a la base de datos ni a webs externas. En desarrollo busca la API en el mismo ordenador que sirve la app, puerto 8000.
- **backend/app/api/** — rutas HTTP. Reciben la petición, validan con `schemas/`, llaman a `services/` y devuelven la respuesta.
- **backend/app/services/** — lógica de negocio: permisos de edición, búsqueda por ingredientes, importación de recetas y vinos desde webs.
- **backend/app/models/** — tablas de PostgreSQL (SQLAlchemy). Cambiarlas exige una migración en `alembic/versions/`.
- **backend/app/i18n/** — textos que ve el usuario, en español e inglés.

## Entornos

| Entorno | Base de datos | API | Cómo |
|---|---|---|---|
| Desarrollo local | PostgreSQL en Docker | `docker compose up` en http://localhost:8000 | `README.md` |
| Producción | PostgreSQL gestionado | Railway o Fly.io (por decidir) | pendiente |
