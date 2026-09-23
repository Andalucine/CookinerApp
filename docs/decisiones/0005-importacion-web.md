# 0005 — Importación de recetas desde páginas web

**Fecha:** 2026-09-23 (sesión 5)

## Contexto
La app debe "leer" una receta de una web y guardarla en el cuaderno conservando el enlace a la fuente. Hay que decidir de dónde se sacan los datos, cómo se protege el servidor y cuándo se guarda la receta. Las reglas de producto (qué planes importan, qué se importa en esta versión) están en la biblia.

## Decisión
- **Fuente de los datos:** los datos de receta en formato schema.org `Recipe` (JSON-LD) que publican casi todas las webs de recetas para los buscadores. Se leen título, descripción, ingredientes, pasos (también por secciones), tiempos, raciones, autor, web, foto y vídeo. Si la página no los tiene (blogs sencillos), se lee su **texto**: la lista que sigue al título "Ingredientes…" (y "para N" como raciones) y los pasos bajo "Preparación / Elaboración / Cómo se hace…" o, si no hay ese título, las líneas numeradas que siguen a los ingredientes; la vista previa avisa de que conviene revisarla (`read_from_text`). Si tampoco hay eso, solo se toman el título y la foto (`no_recipe_data`).
- **Dos pasos:** `POST /imports/recipe` devuelve una **vista previa editable** sin guardar nada; `POST /imports/{job_id}/save` guarda lo que el usuario confirma. La página no se vuelve a descargar al guardar.
- **Ingredientes:** cada línea se separa en cantidad, unidad y nombre con reglas sencillas; `raw_text` conserva la línea original. El nombre se busca en el catálogo (entero y quitando palabras del final, en singular y por alias): "2 dientes de ajo picados" → 2 · diente · ajo.
- **Seguridad:** solo `http`/`https` a direcciones públicas, comprobadas también en cada redirección (nunca `localhost`, la base de datos ni la red interna); 10 s de espera máxima y 3 MB por página.
- **Registro:** cada intento queda en `import_jobs` (`pending` leída, `ok` guardada, `error` con el motivo).
- Sin librerías nuevas para leer HTML (se usa la de Python); `httpx` pasa a ser dependencia de la app.

## Alternativas descartadas
- Reglas propias para cada web: se rompen cada vez que la web cambia su diseño. La lectura del texto es genérica (títulos y listas), no depende de una web concreta.
- Usar una librería de terceros de "scraping" de recetas: añade una dependencia grande para lo que el JSON-LD ya resuelve.
- Guardar directamente sin vista previa: la biblia pide vista previa siempre.

## Consecuencias
- Primera prueba con las webs de la biblia (sesión 5): De Rechupete y Directo al Paladar dan la receta completa por datos estándar; Javi Recetas no los publica y se lee por su texto.
- `scripts/check_import.py` permite comprobar las webs de prueba reales desde el Mac.
- Vinos y vídeos de YouTube como fuente principal se añadirán sobre esta misma base.
