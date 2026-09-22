# Modelo de datos

Estado: **v1** (migración `initial_schema`, sesión 2). Regla: cada cambio en `backend/app/models/` actualiza este documento en el mismo commit.

## Esquema general

```
users ──< group_members >── groups ──< recipes ──< recipe_ingredients >── ingredients
  │            │               │          │
  ├─< auth_identities          │          ├─< recipe_seasons >── seasons
  ├─< password_reset_tokens    │          ├─< recipe_occasions >── occasions
  │                            │          ├─< recipe_editors
  │                            └─< group_invitations       ├─< recipe_contributions
  │                                       │
  └─< import_jobs                         └─< recipe_wines >── wines
```

`A ──< B` significa "un A tiene muchos B". `A >── B` significa que B es catálogo referenciado.

## Usuarios y acceso

| Tabla | Para qué | Campos clave |
|---|---|---|
| `users` | Cuenta de cada persona | `email` (único), `display_name`, `password_hash` (**nulo** si solo entra con Google/Apple), `language` (es/en), `is_active`, `email_verified_at` |
| `auth_identities` | Identificación digital: Google, Apple… | `provider`, `provider_user_id` (únicos juntos), `provider_email` |
| `password_reset_tokens` | "He olvidado mi contraseña" | `token_hash`, `expires_at`, `used_at` |

## Grupos

| Tabla | Para qué | Campos clave |
|---|---|---|
| `groups` | Una familia o grupo de amigos | `name`, `created_by_id` |
| `group_members` | Quién está en cada grupo y con qué rol | `role`: `admin` o `member`; un usuario puede estar en varios grupos |
| `group_invitations` | Código o enlace para entrar en un grupo | `code` (único), `invited_email`, `expires_at`, `accepted_at` |

## Recetas

| Tabla | Para qué | Campos clave |
|---|---|---|
| `recipes` | La receta | `group_id`, `author_id`, `title`, `description`, `instructions`, `prep_time_minutes`, `servings`, `cook_name` (texto libre: "la abuela"), `source_type` (`own`/`web`/`book`/`family`/`other`), `source_name`, `source_url` (**siempre** que venga de la web), `youtube_url`, `image_url`, `language` |
| `ingredients` | Catálogo **global** de ingredientes, nombre normalizado en minúscula y singular | `name` (único), `name_en`, `category` |
| `recipe_ingredients` | Ingredientes de cada receta | `quantity`, `unit`, `raw_text` ("2 tomates maduros"), `position` |
| `seasons` | Las 4 estaciones (precargadas) | `code`, `name_es`, `name_en` |
| `occasions` | Épocas: precargadas (`group_id` nulo, `is_preloaded`) o propias de un grupo | `name_es`, `name_en` |
| `recipe_seasons`, `recipe_occasions` | Una receta puede tener varias estaciones y épocas | — |
| `recipe_editors` | Usuarios autorizados por el autor a editar | — |
| `recipe_contributions` | Lo que otra persona añadió, para mostrar "(añadido por NOMBRE)" | `field`, `content`, `user_id` |

Épocas precargadas: Navidad, Cuaresma, Semana Santa, Feria, Todos los Santos, Verano.

## Vinos

| Tabla | Para qué | Campos clave |
|---|---|---|
| `wines` | Catálogo **global** de vinos | `name`, `winery`, `appellation`, `wine_type` (`red`/`white`/`rose`/`sparkling`/`fortified`/`other`), `grapes`, `vintage`, `tasting_notes`, `pairing_notes`, `source_url` |
| `recipe_wines` | Vinos recomendados para una receta **con el motivo** | `reason`, `origin` (`manual`/`imported`), `added_by_id` |

## Importación

| Tabla | Para qué | Campos clave |
|---|---|---|
| `import_jobs` | Cada intento de importar desde una URL | `kind` (`recipe`/`wine`), `url`, `status` (`pending`/`ok`/`error`), `error_message`, `recipe_id` o `wine_id` resultante |

## Reglas de negocio que el modelo soporta

- Edición de recetas ajenas: autor, `admin` del grupo o alguien en `recipe_editors`.
- Todo lo importado conserva `source_url`.
- Búsquedas: por ingrediente (`recipe_ingredients` → `ingredients`), tiempo (`prep_time_minutes`), cocinero (`author_id` o `cook_name`), fuente (`source_type`/`source_name`), estación y época.

## Convenciones

- Todas las tablas tienen `id` entero autoincremental.
- Fechas con zona horaria (`timestamptz`).
- Borrar un grupo borra en cascada sus recetas, miembros e invitaciones; los catálogos globales (`ingredients`, `wines`, `seasons`) nunca se borran en cascada.
