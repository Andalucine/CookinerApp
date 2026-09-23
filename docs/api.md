# API

La documentación interactiva la genera FastAPI en http://localhost:8000/docs (Swagger) y http://localhost:8000/redoc. Versión 0.3.0 (sesión 4).

## Convenciones

- Peticiones y respuestas en JSON.
- Idioma de los mensajes: cabecera `Accept-Language: es` o `en` (por defecto español). Los catálogos devuelven siempre `name_es` y `name_en`; la app muestra el que toque.
- Endpoints protegidos: cabecera `Authorization: Bearer <access_token>`. El token lo devuelven `/auth/register` y `/auth/login` y dura 30 días.
- Errores: `{"detail": "mensaje para el usuario"}` con el código HTTP correspondiente (401 sin sesión, 403 sin permiso o límite del plan, 404 no encontrado, 409 conflicto, 422 datos inválidos). Una receta de un cuaderno al que no se tiene acceso responde **404**, no 403, para no revelar que existe.
- Permisos sobre un cuaderno: **propietario** (todo), **editor** (añade y edita recetas; sus cambios quedan como contribuciones "añadido por"), **lector** (ve, marca favoritos). Despensa y lista de la compra son siempre las del cuaderno propio.

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
| POST | `/auth/forgot-password` | `email` | 200 siempre. Código de 6 cifras válido 30 minutos (pendiente el envío por correo; en desarrollo sale en el log). |
| POST | `/auth/reset-password` | `email`, `code`, `new_password` | 200 · contraseña cambiada. 400 si el código no vale. |

### Mi cuaderno y compartir (`/notebooks`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/notebooks/mine` | — | Mi cuaderno: `name`, `owner`, `recipe_count`, `shared_with` (personas con acceso), `max_shared_with` del plan (nulo = sin límite). |
| PATCH | `/notebooks/mine` | `name` | Renombrar mi cuaderno. |
| GET | `/notebooks/shared-with-me` | — | Cuadernos ajenos a los que tengo acceso, con `owner` y mi `role` (Ajustes). |
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

### Recetas (`/recipes`)

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| POST | `/recipes` | `title`, `description`, `instructions`, `prep_time_minutes`, `servings`, `cook_name`, `source_type` (`own`/`web`/`book`/`family`/`other`), `source_name`, `source_url` (**obligatorio si `source_type` = `web`**), `youtube_url`, `image_url`, `language`, `ingredients[]` (`name`, `quantity`, `unit`, `raw_text`), `category_ids[]` (la primera es la principal), `tag_ids[]`, `season_ids[]`, `occasion_ids[]`, `notebook_id` (opcional: cuaderno ajeno donde se es editor) | 201 · receta completa. Los ingredientes se buscan en el catálogo por nombre o alias y se crean si no existen. 403 si se supera `max_recipes` del plan o no se es editor del cuaderno. 422 si algún id no existe. |
| GET | `/recipes` | Filtros combinables: `q` (título o descripción), `ingredients` (nombres separados por comas, todos obligatorios, parcial), `max_minutes`, `time` (`quick` ≤ 30 · `medium` 31–60 · `long` > 60), `cook` (cocinero o autor), `source_type`, `source`, `season_id`, `occasion_id`, `category_id` (incluye sus subcategorías), `tag_ids` (comas, todas obligatorias), `favorites=true`, `notebook_id` (cuaderno ajeno con acceso), `all_notebooks=true` (todos los que puedo ver), `limit`, `offset` | `{total, items[]}` con tarjetas: `time_label`, `primary_category`, `author`, `added_by` (nombre si no es el propietario), `is_favorite`. Por defecto busca en el cuaderno propio. |
| GET | `/recipes/{id}` | — | Receta completa con ingredientes, categorías, etiquetas, estaciones y épocas. |
| PUT | `/recipes/{id}` | Mismo cuerpo que POST (sin `notebook_id`) | Sustituye la receta entera. Propietario o editor; si edita un editor, se guardan contribuciones. |
| DELETE | `/recipes/{id}` | — | Solo el propietario del cuaderno o el autor de la receta. |
| POST / DELETE | `/recipes/{id}/favorite` | — | Estrella (idempotente), también en cuadernos ajenos. |

### Mi despensa (`/pantry`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/pantry` | — | Ingredientes que hay en casa, con `location` (`fridge`/`freezer`/`pantry`). |
| POST | `/pantry/items` | `name`, `location` | 201. Repetir un nombre solo actualiza dónde está. |
| DELETE | `/pantry/items/{id}` | — | Quita el ingrediente. |
| GET | `/pantry/what-can-i-cook` | — | `complete[]` (recetas del cuaderno con todo en casa) y `missing_one[]` (falta un solo ingrediente, con `missing[]`). Sal, agua, aceite, pimienta negra y azúcar se dan por hechos. |

### Lista de la compra (`/shopping-list`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/shopping-list` | — | `sections[]` en orden de supermercado, cada una con sus `items[]`; `total` y `pending`. |
| POST | `/shopping-list/items` | `text`, `quantity`, `ingredient_name` | 201. Se coloca en la sección del ingrediente; si es nuevo, en "Otros". |
| POST | `/shopping-list/from-recipe/{recipe_id}` | — | "Añadir lo que me falta": ingredientes de la receta que no están en la despensa ni ya pendientes. |
| POST | `/shopping-list/items/{id}/check` · `/uncheck` | — | Marcar como comprado / desmarcar. |
| DELETE | `/shopping-list/items/{id}` | — | Quitar una línea. |
| DELETE | `/shopping-list/checked` | — | Limpiar lo ya comprado. |

Pendiente: vinos y maridajes, especias (fichas y sustituciones), notas, épocas propias, importación desde webs y YouTube, login con Google/Apple.
