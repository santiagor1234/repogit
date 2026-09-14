# Bot de Telegram (prueba real de pedidos, citas y atención)

La versión "en vivo" de las tres demos de mensajería (`ai-dm-autoresponder`, `pedidos-catalogo`, `citas-booking`), unificadas en un solo bot que **recuerda la conversación** — a diferencia de la primera versión, que trataba cada mensaje aislado y perdía el hilo (ej. clasificaba "2 empanadas y un café" como spam si no venía justo después de decir "quiero pedir").

- `router.py` — decide si el mensaje es un pedido, una cita, o atención general, y mantiene el flujo activo entre mensajes usando `sessions.py` (memoria por chat).
- `bot.py` — conecta ese router a Telegram real vía long polling (no necesita servidor público ni webhook).
- Reutiliza `common/orders.py`, `common/appointments.py` y `common/inbox.py` — la misma lógica que ya prueban las demos simuladas.

**Por qué Telegram para probar (y no WhatsApp directo):** no requiere verificación de negocio, no necesita servidor público, y se crea un bot gratis en menos de 2 minutos. Cuando quieras el canal real, la migración es sencilla (ver el final de este archivo) — el router no cambia, solo cómo entra y sale el mensaje.

## Cómo funciona la conversación

- **Saludo o `/start`:** muestra un menú de botones — 📅 Agendar cita, 🛠️ Servicios, 🕐 Horario, 📍 Ubicación.
- **📅 Agendar cita** (botón de tipo URL): abre la web de reservas real, servida por `automations/booking-api/` — no por texto en el chat. Ver ese README para cómo desplegarla.
- **📍 Ubicación** (botón de tipo URL): abre Google Maps con la dirección de `.env`.
- **🛠️ Servicios / 🕐 Horario** (botones con respuesta en el chat): el bot contesta con texto genérico (`router.services_text()` / `hours_text()`).
- **Pedido:** decís "quiero hacer un pedido" (te muestra el menú) o directo lo que querés con cantidad, ej. "2 empanadas y un café" (lo agrega al carrito sin preguntar nada más). Podés seguir agregando en varios mensajes; el bot recuerda el carrito. Escribí **"eso es todo"** para confirmar y guardar el pedido.
- **Cualquier otra cosa:** cae en atención general (clasifica lead/pregunta/spam y responde con IA), igual que `ai-dm-autoresponder`.
- **"cancelar"** en cualquier momento aborta el pedido en curso.

## Probarlo sin Telegram (más rápido para iterar)

```bash
cd automations/telegram-bot
source ../../venv/bin/activate
python router.py
```

Te deja escribir mensajes directo en la terminal como si fueras el cliente, sin necesitar un bot real. Útil para probar el flujo de pedidos/citas rápido antes de conectar Telegram.

## Setup del bot real (una sola vez)

1. Abre Telegram y busca **@BotFather**.
2. Envíale `/newbot` y seguí las instrucciones (nombre del bot + un username que termine en `bot`, ej. `mi_negocio_bot`).
3. BotFather te da un **token** (algo como `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Cópialo.
4. Agrega el token a tu `.env` (sin pegarlo en el chat conmigo):
   ```
   ! open -e /Users/santiagorodriguezmartinez/automatizaciones-project/.env
   ```
   Completa: `TELEGRAM_BOT_TOKEN=tu_token_aqui`, y de paso `BUSINESS_NAME`, `BUSINESS_ADDRESS`, `BUSINESS_PHONE` (para personalizar el menú/web), y `BOOKING_API_URL` una vez que despliegues `automations/booking-api/` (ver su README) — sin esa última, "Agendar cita" abre una vista previa que no guarda nada real.

## Correr el bot

```bash
cd automations/telegram-bot
source ../../venv/bin/activate
python bot.py
```

Buscá tu bot en Telegram (por el username) y escribile `/start` para ver el menú de opciones, o directo pedile algo. Los pedidos quedan en la misma base que la demo simulada (`pedidos-catalogo/pedidos.db`, revisable con `sqlite3`). Las citas quedan en la base de `automations/booking-api/` (donde esté desplegada — ver `GET /bookings?business=...`), no en `citas-booking/citas.db` (esa es solo de la demo standalone por texto, ya no la usa el bot).

## Limitaciones conocidas de esta versión de prueba

- La memoria de conversación es en RAM: si reiniciás el bot (`Ctrl+C` y volver a correr), se pierde el estado de conversaciones en curso (no los pedidos/citas ya confirmados, esos quedan en SQLite).
- La detección de "quiero pedir X" sin decir antes "pedido" requiere que menciones una cantidad explícita (ej. "2 empanadas"), para evitar falsos positivos con palabras del catálogo que se usan en otro contexto (ej. "tengo un café" hablando de tu propio negocio).
- "cita"/"agendar"/"turno"/"reservar hora"/"servicios"/"horario"/"ubicación" son las palabras que hacen aparecer el menú de botones — mencionar una hora suelta (ej. "abro de 8 am a 7 pm") no lo activa, a propósito, para no confundir una descripción de horario con un pedido de cita.

## Llevarlo a WhatsApp real

- **Twilio WhatsApp Sandbox** (rápido para seguir probando, aún sin aprobación de Meta): reemplazar `get_updates`/`send_message` de `bot.py` por el webhook de Twilio (recibe por HTTP en vez de polling) y `client.messages.create(...)` para enviar. Ahí sí se necesita un servidor público (ngrok para desarrollo, hosting real para producción).
- **Meta WhatsApp Business Platform** (para producción con un cliente real): requiere verificación del negocio, pero es la opción "oficial" y sin intermediario.

En ambos casos, `router.py` (toda la lógica de negocio) se reutiliza tal cual — solo cambia cómo entra y sale el mensaje.
