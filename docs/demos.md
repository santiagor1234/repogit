# Demos

Cinco demos pensadas para servir doble propósito: mostrarle a un cliente potencial de forma visual y rápida, y generar contenido corto para Instagram/TikTok. Se dividen en dos grupos:

- **Con IA (opcional):** `ai-dm-autoresponder`, `lead-finder-outreach`, `content-repurposer` — corren en modo plantilla sin configuración, y mejoran si se agrega una API key en `.env` (copiar de `.env.example`). Prioridad: `GEMINI_API_KEY` (gratis) > `OPENAI_API_KEY` (de pago).
- **Sin IA (100% reglas):** `citas-booking`, `pedidos-catalogo` — no dependen de ninguna API externa. Se eligieron así a propósito para procesos donde la confiabilidad importa más que la naturalidad del texto (agendar, tomar pedidos): más baratas de operar y no pueden "alucinar" un horario o un producto que no existe.

| Demo | Carpeta | Tipo | Gancho de venta | Gancho de contenido |
|---|---|---|---|---|
| AI DM Auto-Responder | `automations/ai-dm-autoresponder` | Con IA | Deja de perder ventas por no responder DMs a tiempo | "Así respondo DMs de clientes mientras duermo" |
| AI Lead Finder + Outreach | `automations/lead-finder-outreach` | Con IA | Prospectos calificados con mensaje personalizado, sin trabajo manual | "Conseguí 8 leads con mensajes personalizados en 1 minuto" |
| Content Repurposer | `automations/content-repurposer` | Con IA | Convierte un video/podcast largo en semanas de contenido corto | "Automaticé cómo creo el contenido de este video" (meta) |
| Agendamiento de Citas | `automations/citas-booking` | Sin IA | Agenda citas solo, entendiendo lenguaje natural, sin doble-booking | "Le escribí pidiendo cita y quedó agendada al toque" |
| Toma de Pedidos | `automations/pedidos-catalogo` | Sin IA | Pedido + total calculado + registrado, sin que nadie lo tipee a mano | "Así tomo pedidos por WhatsApp sin mover un dedo" |

## Por qué estas cinco

- Ninguna depende de un nicho específico — sirven de ejemplo para cualquier tipo de negocio, consistente con la decisión de mantener el nicho amplio (ver `docs/ofertas.md`).
- Todas son demostrables en pantalla en menos de 60 segundos (ideal para Reels/TikTok).
- Cubren distintas etapas del negocio de un cliente: atención (auto-responder), adquisición (lead finder), operación (citas/pedidos), y la operación de este propio negocio (repurposer).
- Mezclan intencionalmente demos "con IA" y "sin IA", para poder explicarle a un cliente que la automatización no siempre significa IA generativa — a veces la solución más confiable y barata es pura lógica de reglas.

## Cómo correrlas

```bash
source venv/bin/activate
python automations/ai-dm-autoresponder/main.py
python automations/lead-finder-outreach/main.py --niche "gimnasios" --city "Medellín"
python automations/content-repurposer/main.py
python automations/citas-booking/main.py
python automations/pedidos-catalogo/main.py
```

Cada demo tiene su propio `README.md` con el detalle de cómo llevarla a producción con un cliente real.

## Probar con un chat real

`automations/telegram-bot/` conecta la misma lógica de `ai-dm-autoresponder` a un bot de Telegram de verdad (setup en su README, vía @BotFather, sin necesidad de servidor público). Es el paso intermedio antes de WhatsApp real: mismo motor, canal real, cero fricción de configuración.
