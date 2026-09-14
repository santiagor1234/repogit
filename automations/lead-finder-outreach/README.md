# AI Lead Finder + Outreach

**El problema que resuelve:** conseguir prospectos calificados y escribirles un primer mensaje personalizado es lento y repetitivo. Este demo genera una lista de leads y un mensaje de contacto personalizado por IA para cada uno, en segundos.

**Por qué es buen gancho de contenido:** "conseguí 8 leads con mensajes personalizados en menos de 1 minuto" es un hook fuerte y fácil de mostrar en pantalla. Funciona para cualquier nicho (basta con cambiar `--niche`), lo que lo hace ideal para no cerrarse a una industria.

**Stack:** Python + Faker (datos de muestra) + OpenAI (opcional) + SQLite/CSV.

> ⚠️ Los leads generados son **sintéticos** (Faker), para que la demo funcione sin depender de una API externa de scraping. Para un cliente real, se conecta a una fuente real (ver abajo).

## Correr la demo

```bash
cd automations/lead-finder-outreach
source ../../venv/bin/activate
python main.py --niche "dentistas" --city "Bogotá" --count 8
```

Prueba también con otros nichos para mostrar versatilidad: `restaurantes`, `gimnasios`, `inmobiliarias`, `abogados`, `veterinarias`, `spa y estética`, `agencias de marketing` (ver `niches.py`) — o cualquier nicho nuevo, que usará un mensaje genérico.

Salida: CSV en `output/` + tabla `prospects` en `leads.db`.

## Llevarlo a producción con un cliente

- Reemplazar `generate_leads()` (Faker) por una fuente real:
  - **Google Maps Places API** (búsqueda por categoría + ciudad).
  - Scraping de un directorio público específico del nicho.
  - Lista propia del cliente (CSV/CRM existente) que solo se enriquece y personaliza.
- Conectar el envío real (email vía SMTP/SendGrid, WhatsApp vía Twilio, o cola de DMs de Instagram) en vez de solo guardar el mensaje.
- Agregar deduplicación y control de frecuencia de envío para evitar spam.
