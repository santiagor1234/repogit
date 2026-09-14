# AI DM Auto-Responder

**El problema que resuelve:** la mayoría de negocios pierden ventas porque no responden DMs de Instagram/WhatsApp a tiempo. Este demo responde al instante, clasifica cada mensaje (lead / pregunta / spam) y guarda automáticamente los leads para seguimiento.

**Por qué es buen gancho de contenido:** funciona para cualquier tipo de negocio (inmobiliaria, clínica, tienda, coach, restaurante, gym — ver `sample_messages.json`), así que es el demo más versátil para mostrar sin verticalizar el nicho. Se presta para un video tipo "así respondo DMs de clientes mientras duermo".

**Stack:** Python + OpenAI (opcional) + SQLite.

## Correr la demo

```bash
cd automations/ai-dm-autoresponder
source ../../venv/bin/activate
python main.py
```

Sin `OPENAI_API_KEY` configurada corre en modo plantilla (igual de demostrable). Con la key en `.env` (ver raíz del proyecto), usa IA real para clasificar y redactar respuestas más naturales.

Los leads quedan en `leads.db` (SQLite), tabla `leads`.

## Probarlo con un chat real (no simulado)

Ver `automations/telegram-bot/` — es la misma lógica de este demo (comparten `common/inbox.py`), pero conectada a un bot de Telegram real que podés probar desde tu celular en minutos, sin necesitar aprobación de negocio ni exponer un servidor.

## Llevarlo a producción con un cliente

- Reemplazar `sample_messages.json` por el webhook real:
  - **WhatsApp:** Twilio WhatsApp API o Meta WhatsApp Business Platform.
  - **Instagram:** Instagram Graph API (mensajería).
- Cambiar SQLite por Postgres (`sql/`) si el cliente necesita más de un usuario/reportería.
- Agregar handoff a humano cuando la IA no esté segura (ej. confianza baja o el cliente pide hablar con una persona).
