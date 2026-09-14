# Automatizaciones Project

Negocio de automatización: servicios para clientes, contenido en redes (Instagram/TikTok) y, en fase futura, productos propios.

## Estructura

- `automations/` — Cada automatización vive en su propia subcarpeta (scripts Python, README con el caso de uso, cliente/demo al que pertenece).
- `n8n_workflows/` — Workflows de n8n exportados como JSON (backup y reutilización de plantillas).
- `sql/` — Esquemas, migraciones y queries usadas por las automatizaciones (ej. tracking de leads, métricas de contenido).
- `content/` — Planeación de contenido para redes.
  - `content/scripts/` — Guiones/hooks de videos individuales.
  - `content/ideas.md` — Banco de ideas de contenido.
  - `content/calendar.md` — Calendario de publicación.
- `docs/` — Documentación de negocio: oferta de servicios, pricing, notas de nicho/posicionamiento.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Variables de entorno (API keys, credenciales de DB, etc.) van en un `.env` local (no se commitea).

## Fases

1. **Servicios + Contenido** — Automatizar procesos para clientes (nicho amplio, sin verticalizar aún) mientras se construye audiencia en Instagram/TikTok mostrando el trabajo.
2. **Productos propios** — Una vez validado qué automatizaciones tienen más demanda, empaquetar como templates/SaaS/cursos.
