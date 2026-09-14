# Booking API

El backend real detrás de la web de reservas (`docs/demos.md`) y del botón "📅 Agendar cita" del bot de Telegram. Antes de esto, la web solo simulaba disponibilidad en el navegador — con esta API, las citas se guardan de verdad y no se puede reservar dos veces el mismo horario.

**Stack:** FastAPI + SQLite. Sin autenticación todavía (ver "Limitaciones" abajo) — suficiente para probar, no para producción con datos sensibles.

## Endpoints

- `GET /health` — chequeo de salud.
- `GET /availability?business=X&date=YYYY-MM-DD` — horarios (9am-5pm, cada 30 min, lunes a viernes) con `available: true/false`.
- `POST /bookings` — body `{business, service, date, time, client_name, phone, note}`. Devuelve `{ok: true, code}` o error 409 si el horario ya está tomado.
- `GET /bookings?business=X` — lista las reservas de un negocio.

## Correr localmente

```bash
cd automations/booking-api
source ../../venv/bin/activate   # o crea un venv propio: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
uvicorn main:app --reload
```

Abre `http://127.0.0.1:8000/health` para confirmar que responde.

## Desplegar en Render (gratis)

1. Sube este proyecto a un repo de GitHub (ver instrucciones que te dio Claude en el chat).
2. En [render.com](https://render.com), crea una cuenta gratis (no pide tarjeta) y conecta tu cuenta de GitHub.
3. **New +** → **Blueprint** → elegí el repo. Render detecta `render.yaml` (en la raíz del proyecto) y configura todo solo.
   - Si preferís configurarlo a mano: **New +** → **Web Service**, elegí el repo, **Root Directory**: `automations/booking-api`, **Build Command**: `pip install -r requirements.txt`, **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`, plan **Free**.
4. Cuando termine el deploy, Render te da una URL pública (algo como `https://booking-api-xxxx.onrender.com`). Cópiala.
5. Avísale a Claude esa URL para conectarla a la web de reservas y al bot de Telegram.

## Conectar Google Sheets (para que el negocio vea sus citas ahí)

Cada reserva nueva se puede mandar automáticamente como fila a un Google Sheet, usando un webhook de Google Apps Script — no requiere crear un proyecto de Google Cloud ni manejar credenciales, todo se configura desde el propio Sheet.

1. Crea un Google Sheet nuevo. En la primera fila, poné los encabezados (en este orden): `date, time, service, client_name, phone, note, code, business, created_at`.
2. **Extensiones → Apps Script**. Borrá el contenido de `Code.gs` y pegá esto:
   ```javascript
   function doPost(e) {
     var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     var data = JSON.parse(e.postData.contents);
     sheet.appendRow([
       data.date, data.time, data.service, data.client_name,
       data.phone, data.note, data.code, data.business, data.created_at
     ]);
     return ContentService.createTextOutput(JSON.stringify({ok: true}))
       .setMimeType(ContentService.MimeType.JSON);
   }
   ```
3. **Implementar → Nueva implementación** → tipo **Aplicación web**. Configurá: **Ejecutar como**: "Yo" (tu cuenta), **Quién tiene acceso**: "Cualquier usuario". Dale a **Implementar**.
4. Google te va a pedir autorizar el script (es tuyo, es seguro). Al final te da una URL que termina en `/exec` — cópiala.
5. Ponela en `.env` local como `GOOGLE_SHEETS_WEBHOOK_URL=esa_url`, y en Render: **Dashboard → booking-api → Environment** → agregá la misma variable con el mismo valor (el `.env` local no llega a Render, hay que configurarlo ahí también).

Cada reserva nueva (desde la web o el bot) va a aparecer como fila en el Sheet en segundos. Si el webhook falla por lo que sea, la reserva igual queda guardada en la base de datos — nunca se pierde una cita por un problema con Sheets.

> Nota: cada negocio nuevo al que le vendas esto necesita su propio Sheet + su propia URL de Apps Script (no se comparte entre clientes). El paso a paso de arriba se repite por cliente.

## Limitaciones del nivel gratis de Render (a tener en cuenta mientras es solo para pruebas)

- El servicio "se duerme" tras ~15 min sin tráfico — la primera consulta después de eso tarda ~30-50s en responder mientras despierta (las siguientes son rápidas).
- El disco no es 100% persistente entre despliegues nuevos (si volvés a hacer `git push` con cambios, las reservas guardadas hasta ese momento pueden perderse). Para operar con clientes reales, hay que pasar a un plan pago con disco persistente (o una base de datos gestionada aparte).
- No hay autenticación en los endpoints — cualquiera con la URL puede leer `/bookings`. Antes de usarlo con un cliente real, agregar una API key simple (header `Authorization`) o migrar a algo con auth propio.
