# Video Generator

Automatiza la creación del video 3 de `content/scripts/03-demo-en-vivo.md` ("te armo la demo de tu negocio ahora mismo"): en vez de grabar la pantalla a mano cada vez, arma el video completo en dos partes — (1) una simulación de la conversación de chat (cliente escribe, aparece el menú de botones, toca "Agendar cita") y (2) el recorrido real de la web de reservas (elige servicio, fecha, hora, completa datos, confirma) — todo grabado en formato vertical, con narración por voz de principio a fin, y entrega un `.mp4` único listo para publicar (~35-40s).

**Por qué esto y no una IA de "texto a video" genérica:** el video muestra el producto real funcionando — eso es lo que lo hace creíble. Un video con avatar/IA genérica se vería falso acá. Lo que sí se automatiza es la parte mecánica (grabar, narrar, armar el archivo), no la autenticidad del contenido.

**Stack:** Playwright (controla el navegador y graba), Gemini TTS (narración, gratis con la misma key que ya usan las otras demos), ffmpeg vía `imageio-ffmpeg` (no necesita Homebrew ni instalar nada aparte).

## Setup

```bash
cd automations/video-generator
source ../../venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # descarga el navegador la primera vez (~1-2 min)
```

## Generar un video

```bash
python main.py --business "Peluquería Estilo" --address "Cra 10 #20-30, Bogotá"
```

Por defecto usa `BOOKING_API_URL` del `.env` (la misma API ya desplegada). El resultado queda en `output/demo_<negocio>_<fecha>.mp4`, listo para subir tal cual o editarle un intro/outro encima en una app de edición si querés pulirlo más.

## Qué hace exactamente

1. Genera primero las dos narraciones (chat + reserva) con Gemini TTS, y mide cuánto dura cada una.
2. **Parte 1 — chat simulado** (`chat_template.html`, una interfaz de chat genérica, no un clon de WhatsApp/Telegram): el cliente "escribe" Hola, aparece el typing..., el bot responde con el saludo y el menú de botones, y se ve el toque en "📅 Agendar cita". La grabación dura al menos lo que tarda su narración (nunca corta el audio a la mitad).
3. **Parte 2 — reserva real**: abre la web de reservas con el nombre/dirección/teléfono del negocio, elige el primer servicio, el primer día y horario disponibles, completa nombre/teléfono de ejemplo ("Cliente Demo"), confirma. Muestra textos superpuestos ("El cliente elige el servicio...", etc.) que quedan grabados en el video.
4. Junta cada parte con su narración, y las dos partes entre sí, en un solo `.mp4` con ffmpeg.

## Notas importantes

- **La reserva que hace es real** (queda en la base de datos del negocio, con nombre "Cliente Demo") — es intencional, ver el código de confirmación real en pantalla es justo lo que hace creíble el video. Si el prospecto se convierte en cliente, limpiar esa fila de prueba antes de entregarle el sistema.
- Si el servicio de Render estaba dormido, la primera carga puede tardar hasta ~50s — el script ya usa timeouts generosos para eso, no hace falta reintentar a mano.
- Sin `GEMINI_API_KEY` configurada, el video sale igual pero sin narración (silencioso, con los textos superpuestos igual).
- Elige siempre el primer servicio/día/horario disponible — si querés otro, por ahora hay que editar `main.py` (`.service-card`, `.day-chip`, `.time-chip` con `nth=0`).

## Próximas mejoras posibles (no implementadas todavía)
- Elegir servicio/fecha/hora específicos por parámetro en vez de siempre el primero.
- Subtítulos de texto sincronizados con la narración (hoy los overlays de la parte de reserva no están timeados palabra por palabra con el audio, solo aproximados).
- Generar en lote una lista de negocios de una vez (ej. desde un CSV) para tener varios videos personalizados listos para outreach.
- Variar el mensaje inicial del cliente en el chat simulado (hoy siempre es "Hola") para tener más variedad entre videos.
