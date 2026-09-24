Utilidades de desarrollo (cargar datos de prueba, limpiar la base de datos, etc.).
Se ejecutan desde `backend/` con `python -m scripts.nombre`.

- `seed_catalogs.py` (+ `catalog_data/`): carga o actualiza los catálogos globales.
- `check_import.py URL…`: comprueba qué lee la importación en páginas reales (no guarda nada).
- `set_plan.py CORREO PLAN`: cambia el plan de una cuenta (`free`, `individual`, `family`) para probar en local lo que depende del plan (vinos, importar de webs). Solo desarrollo, hasta que exista el cobro.
- `sync_dev_schema.py`: pone la base local al día con los modelos **sin borrar datos** (crea las tablas que faltan y añade las columnas nuevas). Alternativa a `docker compose down -v` mientras no haya despliegue; la migración inicial se actualiza igualmente a mano.
- `load_sample_recipes.py CORREO`: añade cuatro recetas de ejemplo (marmitako, torrijas, gazpacho, lentejas) al cuaderno de esa cuenta; las que ya estén no se repiten.

En Docker se escriben con `docker compose exec api` delante, por ejemplo `docker compose exec api python -m scripts.set_plan beatriz@correo.es individual`.
