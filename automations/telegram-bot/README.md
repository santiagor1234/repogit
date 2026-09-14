# Bot de Telegram (prueba real del DM Auto-Responder)

La versión "en vivo" de `ai-dm-autoresponder`, para probar desde tu celular sin necesidad de exponer un servidor a internet. Usa la misma lógica de clasificación + respuesta (`common/inbox.py`), conectada a un bot de Telegram real vía long polling.

**Por qué Telegram para probar (y no WhatsApp directo):**
- No requiere verificación de negocio ni cuenta de WhatsApp Business API.
- No necesita webhook/servidor público (usa "long polling": el bot pregunta por mensajes nuevos, en vez de que Telegram le avise a una URL pública).
- Se crea un bot gratis en menos de 2 minutos.

Cuando quieras el canal real (WhatsApp), la migración es sencilla: la lógica de negocio (`common/inbox.py`) no cambia — solo se reemplaza esta capa de "recibir/enviar mensaje" por la API de WhatsApp (Twilio o Meta). Ver sección final.

## Setup (una sola vez)

1. Abre Telegram y busca **@BotFather**.
2. Envíale `/newbot` y seguí las instrucciones (nombre del bot + un username que termine en `bot`, ej. `mi_negocio_bot`).
3. BotFather te da un **token** (algo como `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Cópialo.
4. Agrega el token a tu `.env` (sin pegarlo en el chat conmigo):
   ```
   ! open -e /Users/santiagorodriguezmartinez/automatizaciones-project/.env
   ```
   Agrega la línea:
   ```
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   BUSINESS_NAME=Nombre de tu negocio de prueba
   ```

## Correr el bot

```bash
cd automations/telegram-bot
source ../../venv/bin/activate
python bot.py
```

Vas a ver en la terminal: `Bot de Telegram — IA real (Gemini)`. Ahora buscá tu bot en Telegram (por el username que le pusiste) y escribile cualquier mensaje, como si fueras un cliente. La respuesta te llega al chat de Telegram al instante, y en la terminal ves la clasificación (lead/pregunta/spam) en tiempo real.

Los leads quedan guardados en `leads.db` (tabla `leads`), igual que en la demo simulada.

## Llevarlo a WhatsApp real

Cuando quieras el canal de verdad para un cliente:

- **Twilio WhatsApp Sandbox** (rápido para seguir probando, aún sin aprobación de Meta): reemplazar `get_updates`/`send_message` por el webhook de Twilio (recibe por HTTP en vez de polling) y `client.messages.create(...)` para enviar. Ahí sí se necesita un servidor público (ngrok para desarrollo, o un hosting real para producción).
- **Meta WhatsApp Business Platform** (para producción con un cliente real): requiere verificación del negocio, pero es la opción "oficial" y sin intermediario.

En ambos casos, `common/inbox.py` (clasificar + redactar respuesta) se reutiliza tal cual — solo cambia cómo entra y sale el mensaje.
