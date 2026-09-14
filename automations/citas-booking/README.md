# Agendamiento de Citas Automático

**El problema que resuelve:** agendar citas a mano (leer el mensaje, revisar el calendario, confirmar) es lento y se presta a errores/doble-booking. Este demo entiende la preferencia de fecha/hora del cliente en lenguaje natural, busca el espacio libre más cercano y agenda solo, sin intervención humana.

**Por qué es buen gancho de venta:** aplica a cualquier negocio que agende (clínicas, spas, consultorios, talleres, coaches, veterinarias, barberías...) y el "wow" es inmediato: el cliente escribe en lenguaje natural y la cita queda agendada al instante.

**Importante — esta automatización es 100% basada en reglas, no usa IA.** Es intencional: agendar es un proceso crítico donde preferimos que falle de forma clara ("no encontramos disponibilidad") a que una IA "alucine" un horario incorrecto. Además así no tiene costo por mensaje ni depende de que una API esté arriba.

**Stack:** Python (regex + reglas de fecha/hora) + SQLite.

## Correr la demo

```bash
cd automations/citas-booking
source ../../venv/bin/activate
python main.py
```

Genera un calendario de disponibilidad de las próximas 2 semanas (lunes a viernes, 9am-4pm) en `citas.db`, y agenda las 4 solicitudes de `sample_requests.json` según lo que cada cliente pidió (día específico, "mañana", "lo antes posible", etc.).

## Probarlo con un chat real (no simulado)

Ver `automations/telegram-bot/` — si el cliente no dice el día en el primer mensaje, el bot se lo pregunta y espera la respuesta en el siguiente mensaje (acá, en cambio, cada solicitud se procesa de una sola vez). Comparte el mismo calendario (`citas.db`), así que no hay doble-booking entre ambas.

## Llevarlo a producción con un cliente

- Reemplazar `sample_requests.json` por el webhook real de WhatsApp/Instagram.
- Sincronizar la tabla `slots` con el calendario real del negocio (Google Calendar API / Calendly API) en vez de vivir solo en SQLite.
- Agregar recordatorio automático 24h antes (otra automatización aparte, reutilizable) y opción de cancelar/reprogramar respondiendo al mismo mensaje.
- Si se quiere entender frases más ambiguas, se puede agregar una capa opcional de IA (`common/ai.py`) **solo como respaldo** cuando el parser de reglas no detecta nada — nunca como reemplazo, para no perder la confiabilidad.
