# Demos

Tres demos pensadas para servir doble propósito: mostrarle a un cliente potencial de forma visual y rápida, y generar contenido corto para Instagram/TikTok. Todas corren sin configuración (modo plantilla) y mejoran si se agrega `OPENAI_API_KEY` en `.env` (copiar de `.env.example`).

| Demo | Carpeta | Gancho de venta | Gancho de contenido |
|---|---|---|---|
| AI DM Auto-Responder | `automations/ai-dm-autoresponder` | Deja de perder ventas por no responder DMs a tiempo | "Así respondo DMs de clientes mientras duermo" |
| AI Lead Finder + Outreach | `automations/lead-finder-outreach` | Prospectos calificados con mensaje personalizado, sin trabajo manual | "Conseguí 8 leads con mensajes personalizados en 1 minuto" |
| Content Repurposer | `automations/content-repurposer` | Convierte un video/podcast largo en semanas de contenido corto | "Automaticé cómo creo el contenido de este video" (meta) |

## Por qué estas tres

- Ninguna depende de un nicho específico — sirven de ejemplo para cualquier tipo de negocio, consistente con la decisión de mantener el nicho amplio (ver `docs/ofertas.md`).
- Las tres son demostrables en pantalla en menos de 60 segundos (ideal para Reels/TikTok).
- Cubren las tres etapas del embudo de un negocio: atención al cliente (auto-responder), adquisición (lead finder), y la operación propia de este negocio (repurposer).

## Cómo correrlas

```bash
source venv/bin/activate
python automations/ai-dm-autoresponder/main.py
python automations/lead-finder-outreach/main.py --niche "gimnasios" --city "Medellín"
python automations/content-repurposer/main.py
```

Cada demo tiene su propio `README.md` con el detalle de cómo llevarla a producción con un cliente real.
