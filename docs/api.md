# API

La documentación interactiva la genera FastAPI en http://localhost:8000/docs (Swagger) y http://localhost:8000/redoc. Versión 0.8.0 (sesión 9).

## Convenciones

- Peticiones y respuestas en JSON.
- Idioma de los mensajes: cabecera `Accept-Language` con `es`, `en`, `fr`, `nl` o `de` (por defecto español; sesión 9). Los catálogos devuelven `name_es`, `name_en` y, desde la fase 2 de la sesión 9, `name_fr`, `name_nl` y `name_de` (lo mismo con `substitute_`, `note_`, `situation_`, `equivalence_`, `quick_substitute_`, `reason_`); estos tres pueden venir vacíos en lo que un cuaderno escribió a mano, y entonces la app enseña el inglés.
- Endpoints protegidos: cabecera `Authorization: Bearer <access_token>`. El token lo devuelven `/auth/register` y `/auth/login` y dura 30 días.
- Errores: `{"detail": "mensaje para el usuario"}` con el código HTTP correspondiente (401 sin sesión, 403 sin permiso o límite del plan, 404 no encontrado, 409 conflicto, 422 datos inválidos). Una receta de un cuaderno al que no se tiene acceso responde **404**, no 403, para no revelar que existe.
- Permisos sobre un cuaderno: **propietario** (todo), **editor** (añade y edita recetas, notas y épocas propias, y recomienda vinos en sus recetas; queda marcado "añadido por" / "editado por"; borra solo lo que añadió él), **lector** (ve, marca favoritos). Despensa y lista de la compra son siempre las del cuaderno propio.
- Cualquier elemento (receta, nota, época) de un cuaderno sin acceso responde **404**.
- Vinos (sesión 9): la bodega es el catálogo de **Vinoselección**, el mismo para todos los cuadernos y todos los planes (la app actúa como agente de ventas de la tienda). Desde la API no se crean, cambian ni borran vinos: los carga y actualiza `scripts.sync_vinoseleccion`.

## Endpoints

### Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Comprueba que la API y la base de datos responden. |

### Acceso (`/auth`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/auth/register` | `email`, `display_name`, `password` (mín. 8), `language` | 201 · `access_token` + `user` (con `plan`, `max_recipes`, `max_shared_with`, `notebook_id`). Crea la cuenta en el plan gratuito **y su cuaderno**. 409 si el correo ya existe. |
| POST | `/auth/login` | `email`, `password` | 200 · `access_token` + `user`. 401 si no coinciden. |
| GET | `/auth/me` | — | Datos del usuario conectado. |
| PATCH | `/auth/me` | `language` (`es`/`en`/`fr`/`nl`/`de`) | Cambia el idioma de la cuenta desde Mi cuenta (sesión 8; cinco idiomas desde la sesión 9). |
| POST | `/auth/forgot-password` | `email` | 200 siempre. Código de 6 cifras válido 30 minutos (pendiente el envío por correo; en desarrollo sale en el log). |
| POST | `/auth/reset-password` | `email`, `code`, `new_password` | 200 · contraseña cambiada. 400 si el código no vale. |

### Mi cuaderno y compartir (`/notebooks`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/notebooks/mine` | — | Mi cuaderno: `name`, `owner`, `recipe_count`, `shared_with` (personas con acceso), `max_shared_with` del plan (nulo = sin límite). |
| PATCH | `/notebooks/mine` | `name` | Renombrar mi cuaderno. |
| GET | `/notebooks/shared-with-me` | — | Cuadernos ajenos a los que tengo acceso, con `owner` y mi `role` (Mi cuenta). |
| POST | `/notebooks/mine/invitations` | `role` (`viewer`/`editor`), `email` (opcional: solo esa cuenta podrá usar el código) | 201 · `code` de 8 caracteres (sin 0/O/1/I), válido 7 días, una persona por código. 403 si el plan no permite más personas. |
| GET | `/notebooks/mine/invitations` | — | Invitaciones pendientes (no usadas ni caducadas). |
| DELETE | `/notebooks/mine/invitations/{id}` | — | Anular una invitación. |
| POST | `/notebooks/join` | `code` | "Unirme a un cuaderno". 200 · el cuaderno y mi rol. 400 si el código no vale, caducó, ya se usó, es de otro correo o de mi propio cuaderno; 403 si el cuaderno ya tiene todas las personas de su plan. Si ya tenía acceso, el nuevo código **cambia mi rol**. |
| GET | `/notebooks/mine/access` | — | Personas con acceso a mi cuaderno y su rol. |
| PATCH | `/notebooks/mine/access/{user_id}` | `role` | Cambiar el rol de alguien. |
| DELETE | `/notebooks/mine/access/{user_id}` | — | Quitar el acceso a alguien. |
| DELETE | `/notebooks/{notebook_id}/access/me` | — | Salir por mí mismo de un cuaderno ajeno. |

### Catálogos (`/catalog`, sin login)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/catalog/categories` | Árbol completo de categorías de recetas (`children` anidados, `level` 1-3, `examples_es`). |
| GET | `/catalog/tags?kind=` | Etiquetas; `kind` opcional: `course`, `method`, `diet`, `difficulty`, `origin`. |
| GET | `/catalog/seasons` | Las 4 estaciones. |
| GET | `/catalog/occasions` | Épocas precargadas. |
| GET | `/catalog/shopping-sections` | Secciones del supermercado en orden de recorrido. |
| GET | `/catalog/ingredients?q=` | Autocompletar ingredientes por nombre o alias (`hierbabuena` → menta). |
| GET | `/catalog/wine-categories` | Árbol de tipos de vino (dos niveles) con `serving_temp`. |
| GET | `/catalog/wine-facets` | Valores de dulzor, cuerpo, crianza (con `name_es`/`name_en`) y precio. |

### Recetas (`/recipes`)

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| POST | `/recipes` | `title`, `description`, `instructions`, `prep_time_minutes`, `servings`, `cook_name`, `source_type` (`own`/`web`/`book`/`family`/`other`), `source_name`, `source_url` (**obligatorio si `source_type` = `web`**), `youtube_url`, `image_url`, `language`, `ingredients[]` (`name`, `quantity`, `unit`, `raw_text`), `category_ids[]` (la primera es la principal), `tag_ids[]`, `season_ids[]`, `occasion_ids[]`, `notebook_id` (opcional: cuaderno ajeno donde se es editor) | 201 · receta completa. Los ingredientes se buscan en el catálogo por nombre o alias y se crean si no existen. 403 si se supera `max_recipes` del plan o no se es editor del cuaderno. 422 si algún id no existe o si una época propia es de otro cuaderno. |
| GET | `/recipes` | Filtros combinables: `q` (título o descripción), `ingredients` (nombres separados por comas, todos obligatorios, parcial), `max_minutes`, `time` (`quick` ≤ 30 · `medium` 31–60 · `long` > 60), `cook` (cocinero o autor), `source_type`, `source`, `season_id`, `occasion_id`, `category_id` (incluye sus subcategorías), `tag_ids` (comas, todas obligatorias), `favorites=true`, `notebook_id` (cuaderno ajeno con acceso), `all_notebooks=true` (todos los que puedo ver), `limit`, `offset` | `{total, items[]}` con tarjetas: `time_label`, `primary_category`, `author`, `added_by` (nombre si no es el propietario), `is_favorite`. Por defecto busca en el cuaderno propio. |
| GET | `/recipes/category-counts` | `notebook_id` (opcional) | `[{category_id, count}]`: recetas del cuaderno en cada categoría, contando sus subcategorías (cada receta una vez por categoría). Las categorías sin recetas no aparecen. Para los números del árbol en la app. |
| GET | `/recipes/{id}` | — | Receta completa con ingredientes, categorías, etiquetas, estaciones y épocas; además `notebook_owner` (nombre del propietario del cuaderno, para "Receta del cuaderno de NOMBRE") y `my_role` (`owner`/`editor`/`viewer`: lo que puede hacer quien pregunta). |
| PUT | `/recipes/{id}` | Mismo cuerpo que POST (sin `notebook_id`) | Sustituye la receta entera. Propietario o editor; si edita un editor, se guardan contribuciones. |
| DELETE | `/recipes/{id}` | — | Solo el propietario del cuaderno o el autor de la receta. |
| POST / DELETE | `/recipes/{id}/favorite` | — | Estrella (idempotente), también en cuadernos ajenos. |
| GET | `/recipes/{id}/spices` | — | Ingredientes de la receta con ficha de especia, `in_my_pantry` y sus sustitutos, cada uno con `in_my_pantry` (despensa **propia**). |
| GET | `/recipes/{id}/wines` | — | `recommended[]` (vino, `reason`, `origin`, `added_by`) y, si no hay ninguno, `suggestion`: `based_on` (categoría usada), `wine_types[]` con motivo y `wines[]`: hasta 6 vinos de Vinoselección de esos tipos, primero los favoritos de quien mira y después los que están a la venta (sesión 9). |
| POST | `/recipes/{id}/wines` | `wine_id`, `reason` | 201 · Recomendar un vino de la bodega de Vinoselección (404 si no existe); repetirlo cambia el motivo. Propietario o editor. |
| DELETE | `/recipes/{id}/wines/{link_id}` | — | Quitarlo de la receta (el vino sigue en la bodega). Propietario o quien lo recomendó. |

### Mi despensa (`/pantry`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/pantry` | — | Ingredientes que hay en casa, con `location` (`fridge`/`freezer`/`pantry`). |
| POST | `/pantry/items` | `name`, `location` | 201. Repetir un nombre solo actualiza dónde está. |
| PATCH | `/pantry/items/{id}` | `image_url` | Pone una foto a lo que hay (`null` la quita), sesión 9. |
| DELETE | `/pantry/items/{id}` | — | Quita el ingrediente. |
| GET | `/pantry/what-can-i-cook` | — | `complete[]` (recetas del cuaderno con todo en casa) y `missing_one[]` (falta un solo ingrediente, con `missing[]`). Sal, agua, aceite, pimienta negra y azúcar se dan por hechos. |

### Lista de la compra (`/shopping-list`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/shopping-list` | — | `sections[]` en orden de supermercado, cada una con sus `items[]`; `total` y `pending`. |
| POST | `/shopping-list/items` | `text`, `quantity`, `ingredient_name` | 201. Se coloca en la sección que el cuaderno eligió para ese ingrediente, si la eligió; si no, en la del catálogo (plurales incluidos: "patatas" → patata); si es nuevo, en "Otros". |
| GET | `/shopping-list/from-recipe/{recipe_id}` | — | Antes de añadir (sesión 9): los ingredientes de la receta con lo que es cada uno para mí: `missing`, `in_pantry`, `pending` o `staple`, con `quantity` (lo que dice la receta). |
| POST | `/shopping-list/from-recipe/{recipe_id}` | `ingredient_ids` (opcional) | "Añadir a la compra": sin cuerpo, lo que falta (ni en la despensa ni pendiente ni básico); con `ingredient_ids`, exactamente los marcados (aunque estén en la despensa), saltando solo lo ya pendiente. |
| POST | `/shopping-list/items/{id}/check` · `/uncheck` | — | Marcar como comprado / desmarcar. |
| PATCH | `/shopping-list/items/{id}` | `section_code` y/o `image_url` | Llevar la línea a otra sección y/o ponerle una foto del producto (`image_url: null` la quita), sesión 9. El cuaderno lo recuerda para ese ingrediente y mueve también sus otras líneas pendientes. 404 si la sección no existe. |
| DELETE | `/shopping-list/items/{id}` | — | Quitar una línea. |
| DELETE | `/shopping-list/checked` | `to_pantry` (opcional) | Limpiar lo ya comprado. Con `to_pantry=true` (sesión 9), antes lo apunta en la despensa: congelados al congelador; frutas y verduras, carnes, pescados y lácteos a la nevera; lo demás a la despensa. |

### Especias (`/spices`, sin login)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/spices/families?notebook_id=` | Las 7 familias en su orden, con nombre y número de especias (con token, cuenta también las del cuaderno). |
| GET | `/spices?family=&q=&notebook_id=` | Lista de especias; `q` busca en nombre, alias e inglés. Indica `has_substitutions` e `is_blend`. Con token, añade las mezclas y las especias del cuaderno (`notebook_blend_id`, `is_own_version`, `notebook_spice_id`, `added_by`) y tiene en cuenta sus sustitutos propios; `notebook_id` para un cuaderno ajeno al que se tiene acceso (sesión 8). |
| GET | `/spices/rules` | Reglas generales de equivalencia (fresca → seca…). |
| GET | `/spices/blends` | Las mezclas con su composición (`parts`, `is_optional`). |
| GET | `/spices/{ingredient_id}?notebook_id=` | Ficha: `substitutions[]` (proporción y nota), `blend` si es mezcla, `used_in_blends[]`. También ajo, cebolla y jengibre fresco. 404 si no tiene ficha. Con token, `blend` es la versión del cuaderno si la tiene y `catalog_blend` la del catálogo; `substitutions` es la lista propia del cuaderno cuando existe (`has_own_substitutions`, `substitutions_added_by`); `pairs_with` ("va bien con") en el idioma pedido, o el texto propio del cuaderno (`has_own_pairs_with`) (sesión 8). |

### Mezclas del cuaderno (`/blends`, sesión 8)

Mezclas propias del cuaderno y versiones propias de las del catálogo. Propietario y editores las cambian; borra el propietario o quien la creó. Sin límite de plan.

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/blends?notebook_id=` | — | Las mezclas del cuaderno (por defecto el mío). |
| POST | `/blends` | `name`, `note`, `items[]` (`name`, `parts`, `is_optional`), `notebook_id` opcional | 201 · la mezcla. Si el nombre es el de una mezcla del catálogo, es la **versión del cuaderno**. 409 si el cuaderno ya tiene una con ese nombre; 422 si se lleva a sí misma. |
| PUT | `/blends/{id}` | igual que POST (sin `notebook_id`) | La mezcla con sus nuevos ingredientes. |
| DELETE | `/blends/{id}` | — | Borra la mezcla; para una versión del catálogo, vuelve a la del catálogo. |

### Especias y sustitutos del cuaderno (`/notebook-spices`, sesión 8)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/notebook-spices?notebook_id=` | — | Las especias añadidas por el cuaderno. |
| POST | `/notebook-spices` | `name`, `family` (código de las 7), `aliases`, `notebook_id` opcional | 201 · la especia. 409 si el nombre ya es una especia del catálogo o del cuaderno. |
| PUT | `/notebook-spices/{id}` | `name`, `family`, `aliases` | La especia. |
| DELETE | `/notebook-spices/{id}` | — | Borra la especia del cuaderno y su lista de sustitutos. |
| PUT | `/notebook-spices/{ingredient_id}/substitutions` | `items[]` (`substitute`, `ratio`, `note`), `notebook_id` opcional | La lista propia del cuaderno para ese ingrediente (sustituye a la del catálogo). Si el sustituto es un solo nombre del catálogo, se enlaza (`substitute_id`). 422 si es la propia especia. |
| DELETE | `/notebook-spices/{ingredient_id}/substitutions?notebook_id=` | — | Vuelve a la lista del catálogo. 404 si no había lista propia. |
| PUT | `/notebook-spices/{ingredient_id}/pairs-with` | `pairs_with` (texto, alimentos separados por comas), `notebook_id` opcional | El "va bien con" propio del cuaderno para ese ingrediente. |
| DELETE | `/notebook-spices/{ingredient_id}/pairs-with?notebook_id=` | — | Vuelve al texto del catálogo. 404 si no había texto propio. |

### Vinos (`/wines`)

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| GET | `/wines` | `q` (nombre, bodega, uva, denominación), `category_id` (un tipo de primer nivel incluye sus hijos), `sweetness`, `body`, `ageing`, `country`, `appellation`, `grape`, `price_range`, `favorites=true`, `in_stock=true` (solo lo que se puede comprar), `limit`, `offset` | `{total, items[]}`, primero lo que está a la venta. Cada vino lleva `category` (y su `parent`), `source_name` ("Vinoselección"), `source_price`, `in_stock`, `shop_url` (su ficha en la tienda **con el código de agente**, variable de entorno `SHOP_LINK_PARAMS`) e `is_favorite`. |
| GET | `/wines/category-counts` | — | Vinos a la venta por tipo (un tipo de primer nivel cuenta sus subtipos), para "Por tipos". |
| GET | `/wines/{id}/recipes` | `notebook_id` (por defecto, el propio) | Recetas **de ese cuaderno** para las que se recomienda el vino, con `reason` y `added_by`. |
| ~~POST~~ | ~~`/imports/wine`~~ | — | Retirado en la sesión 9: los vinos ya no se importan uno a uno; la bodega es la de Vinoselección. El lector de fichas de vino sigue en `app/services/wine_importer.py` y lo usa `scripts.sync_vinoseleccion`. |
| GET | `/wines/{id}` | — | Ficha: lo de la lista más facetas, uvas, notas de cata, maridaje, `pairs_with_categories` y `checked_at` (última vez que se leyó su página). `POST /wines` y `PUT`/`DELETE /wines/{id}` ya no existen (405, sesión 9). |
| POST / DELETE | `/wines/{id}/favorite` | — | Estrella, también como lector. |

### Menú semanal (`/menus`, sesión 9)

Siempre el cuaderno propio. Sin inteligencia artificial: reglas sobre categorías, etiquetas, estación y despensa (decisión sesión 8).

| Método | Ruta | Cuerpo / parámetros | Qué hace |
|---|---|---|---|
| GET | `/menus/check` | `week_start` | Antes del borrador: `season` de esa semana, `total_recipes`, `breakfast_recipes` (etiqueta momento = desayuno) y `main_recipes` (el resto, que valen para comida y cena). |
| GET | `/menus` | `week_start` (cualquier día de la semana) | El menú de esa semana (`slots[]` con `day` 0–6, `meal`, `recipe` o `note`), o 404 si aún no hay. |
| POST | `/menus/draft` | `week_start`, `meals` (`breakfast`/`lunch`/`dinner`), `wants` (alimentos separados por comas, opcional) | 201: el borrador de la semana (sustituye al de esa semana si lo había). Reglas, por orden: desayuno solo con recetas etiquetadas desayuno; **comida y cena solo con platos principales** (rama Salado, sin aperitivos, salsas, panes, caldos ni guarniciones, y sin las etiquetadas postre, aperitivo o merienda; `no_main_recipes` si no hay ninguno); no repetir receta mientras queden sin usar, y **como máximo dos veces por semana** (después el plato queda vacío: `not_enough_recipes`; los desayunos sí se repiten); los alimentos de `wants` primero (en ingredientes, título y nombre de categoría); **cena ligera** (etiqueta "cena ligera", ensaladas, sopas, huevos, verduras, pescados o hasta 30 minutos) y **comida contundente** (guisos, legumbres, carnes, arroces, pasta) como preferencia; estación de la semana como preferencia (`season_ignored` si entra alguna de otra estación); no dos platos seguidos de la misma categoría el mismo día; entre iguales, lo que permite la despensa. `notices[]`: `no_breakfast_recipes` (huecos de desayuno vacíos), `filled_with_rest` (no había bastantes recetas con esos alimentos), `season_ignored`, `repeated` (cuaderno pequeño: alguna receta se repite). |
| PUT | `/menus/{id}/slots/{slot_id}` | `recipe_id` (del cuaderno propio) y/o `note` | Cambiar un plato: elegir una receta, escribirlo a mano o dejarlo vacío (`recipe_id: null`, `note: null`). 404 si la receta es de otro cuaderno. |
| POST | `/menus/{id}/slots/{slot_id}/another` | — | "Otra propuesta" para ese plato, evitando las recetas que ya están en la semana cuando hay bastantes. |
| GET | `/menus/{id}/shopping` | — | Antes de añadir: todos los ingredientes de las recetas de la semana, una vez cada uno, con su estado (`missing`, `in_pantry`, `pending`, `staple`), las cantidades que dicen las recetas y `recipes[]` (qué recetas lo usan). |
| POST | `/menus/{id}/shopping` | `ingredient_ids` (opcional) | "Añadir a la compra lo de toda la semana": sin cuerpo, lo que falta; con `ingredient_ids`, exactamente los marcados. `added[]` y `recipes` (recetas miradas). |
| DELETE | `/menus/{id}` | — | Borrar el menú de la semana. |

### Fotos (`/photos`, sesión 9)

| Método | Ruta | Cuerpo | Qué hace |
|---|---|---|---|
| POST | `/photos` | `file` (multipart: JPEG, PNG, WebP o HEIC, hasta 10 MB) | 201 con `url` (`/photos/1f3….jpg`) para guardar en el `image_url` de una receta, un vino, un producto de la despensa o una línea de la compra. 415 si no es una foto, 413 si pesa más. |
| GET | `/photos/{nombre}` | — | La foto, sin sesión (el móvil la muestra como una imagen cualquiera). En desarrollo los archivos están en la carpeta `uploads/` del proyecto (fuera de git); en producción irán a un almacén de archivos. |

### Notas (`/notes`)

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| GET | `/notes` | `notebook_id`, `q` (título o contenido), `kind` | Notas más recientes primero, con `kind`, `preview`, `author_id` (quién la escribió: la app ofrece Borrar al propietario y a esa persona; sesión 9), `added_by`, `edited_by`. |
| POST | `/notes` | `title`, `content`, `kind` (opcional: `recipes`, `wines`, `spices`, `celebrations`, `shopping`, `ideas`; sesión 9), `notebook_id` (opcional) | 201. Propietario o editor. |
| GET / PUT / DELETE | `/notes/{id}` | PUT: `title`, `content`, `kind` | Borrar: propietario o autor. |

### Épocas (`/occasions`)

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| GET | `/occasions` | `notebook_id` | Precargadas (en su orden) y después las propias del cuaderno por orden alfabético, con `notebook_id` y `added_by`. |
| POST | `/occasions` | `name`, `notebook_id` (opcional) | 201. 409 si ya existe (sin distinguir mayúsculas, también frente a las precargadas). |
| PUT | `/occasions/{id}` | `name` | Renombrar. 403 si es precargada. |
| DELETE | `/occasions/{id}` | — | Propietario o quien la creó; las recetas se quedan sin esa época. 403 si es precargada. |

### Importar recetas de la web (`/imports`)

Solo en cuadernos cuyo propietario tiene plan individual o familiar (403 en uno gratuito); propietario o editor. Detalles en la decisión 0005.

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/imports/recipe` | `url`, `notebook_id` (opcional) | Vista previa **sin guardar**: `job_id`, `complete`, `warnings[]` (`no_recipe_data`, `read_from_text` —leída del texto de la página, revisar—, `no_ingredients`, `no_instructions`, `no_time`) y `recipe` (mismo formato que `POST /recipes`, con `source_type` = `web`, `source_url`, `source_name`, `cook_name`, `youtube_url`). 422 si la dirección no vale o no hay receta; 502 si no se puede abrir la página. |
| POST | `/imports/{job_id}/save` | `recipe` (la vista previa, editada o no) | 201 · receta guardada en el cuaderno elegido al importar. 409 si ya se guardó; 422 si falta el enlace a la fuente. |
| GET | `/imports` | — | Mis últimos 20 intentos (`status`: `pending`, `ok`, `error`). |

Pendiente: importación de vídeos de YouTube, login con Google/Apple.
