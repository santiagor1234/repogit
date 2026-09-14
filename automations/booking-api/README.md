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

## Limitaciones del nivel gratis de Render (a tener en cuenta mientras es solo para pruebas)

- El servicio "se duerme" tras ~15 min sin tráfico — la primera consulta después de eso tarda ~30-50s en responder mientras despierta (las siguientes son rápidas).
- El disco no es 100% persistente entre despliegues nuevos (si volvés a hacer `git push` con cambios, las reservas guardadas hasta ese momento pueden perderse). Para operar con clientes reales, hay que pasar a un plan pago con disco persistente (o una base de datos gestionada aparte).
- No hay autenticación en los endpoints — cualquiera con la URL puede leer `/bookings`. Antes de usarlo con un cliente real, agregar una API key simple (header `Authorization`) o migrar a algo con auth propio.
