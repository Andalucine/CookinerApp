# 0003 — Login con contraseña e identificación digital

**Fecha:** 2026-09-22  
**Nota (sesión 4):** la parte de grupos e invitaciones a grupos queda sustituida por la decisión [0004](0004-cuaderno-personal.md): ahora se invita a un cuaderno con rol lector o editor (`notebook_invitations`). El resto sigue vigente.

## Contexto
La app la usarán personas con distinta capacitación digital. Hay que decidir cómo entran.

## Decisión
- Dos formas de entrar, desde el principio: **email + contraseña** e **identificación digital** (Google y Apple; en el móvil, Face ID / huella para no teclear).
- La contraseña es opcional en `users` (`password_hash` nulo si solo se usa identidad externa). Las identidades externas van en `auth_identities`.
- La pantalla de acceso lleva siempre **"ver contraseña"** (ojo en el campo) y **"He olvidado mi contraseña"** (código por correo con caducidad, tabla `password_reset_tokens`).
- Entrada a un grupo por invitación (`group_invitations`).

## Alternativas descartadas
- Solo contraseña: más fricción para usuarios básicos.
- Solo identidad externa: deja fuera a quien no tiene cuenta Google/Apple.
- Certificado digital / Cl@ve: pensado para trámites con la administración, no para una app familiar.

## Consecuencias
- Hace falta dar de alta la app en Google Cloud y en Apple Developer para obtener las claves de login (sesión de la app móvil).
- Hace falta un servicio de envío de correo para "contraseña olvidada" (se decidirá en la sesión de despliegue).
