# API

La documentación interactiva la genera FastAPI en http://localhost:8000/docs (Swagger) y http://localhost:8000/redoc.

## Convenciones

- Peticiones y respuestas en JSON.
- Idioma de los mensajes: cabecera `Accept-Language: es` o `en` (por defecto español).
- Endpoints protegidos: cabecera `Authorization: Bearer <access_token>`. El token lo devuelven `/auth/register` y `/auth/login` y dura 30 días.
- Errores: `{"detail": "mensaje para el usuario"}` con el código HTTP correspondiente (401 sin sesión, 403 sin permiso, 404 no encontrado, 409 conflicto, 422 datos inválidos).

## Endpoints

### Sistema

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Comprueba que la API y la base de datos responden. Devuelve `{"status": "ok"}`. |

### Acceso (`/auth`)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| POST | `/auth/register` | `email`, `display_name`, `password` (mín. 8), `language` (`es`/`en`) | 201 · `access_token` + `user`. 409 si el correo ya existe. |
| POST | `/auth/login` | `email`, `password` | 200 · `access_token` + `user`. 401 si no coinciden. |
| GET | `/auth/me` | — (requiere token) | Datos del usuario conectado. |
| POST | `/auth/forgot-password` | `email` | 200 siempre (no revela si el correo existe). Genera un código de 6 cifras válido 30 minutos. **Pendiente:** envío por correo; en desarrollo el código sale en el log de la API. |
| POST | `/auth/reset-password` | `email`, `code`, `new_password` | 200 · contraseña cambiada. 400 si el código no vale o caducó. Cada código se usa una sola vez. |

Pendiente: login con Google/Apple (`auth_identities`), grupos, recetas, ingredientes, vinos, importación.
