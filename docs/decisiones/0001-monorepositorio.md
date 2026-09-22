# 0001 — Monorepositorio

**Fecha:** 2026-09-22

## Contexto
CookinerApp tiene dos partes: una API (Python/FastAPI) y una app móvil (Expo/React Native). Hay que decidir si viven en uno o dos repositorios.

## Decisión
Un único repositorio `CookinerApp` con `backend/` y `mobile/` como carpetas de primer nivel.

## Alternativas descartadas
- Dos repositorios (`cookinerapp-api`, `cookinerapp-mobile`): más limpio para equipos grandes, pero obliga a coordinar dos historiales y dos clones para cada cambio que toca API y app a la vez.

## Consecuencias
- Un solo clon, un solo historial, un solo sitio donde mirar.
- Los cambios de API y app que van juntos se suben en el mismo commit.
- El `.gitignore` de la raíz cubre Python, Node y macOS.
