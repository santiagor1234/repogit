# Video Generator

Automatiza la creación del video 3 de `content/scripts/03-demo-en-vivo.md` ("te armo la demo de tu negocio ahora mismo"): en vez de grabar la pantalla a mano cada vez, un navegador controlado hace el recorrido completo de la web de reservas (elige servicio, fecha, hora, completa datos, confirma), lo graba en formato vertical, le agrega narración por voz, y entrega un `.mp4` listo para publicar.

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

1. Abre la web de reservas con el nombre/dirección/teléfono del negocio que le pases.
2. Va clickeando: elige el primer servicio, el primer día disponible, el primer horario disponible, completa nombre/teléfono de ejemplo ("Cliente Demo"), confirma.
3. Va mostrando textos superpuestos ("El cliente elige el servicio...", etc.) que quedan grabados en el video.
4. Genera una narración en español con Gemini TTS describiendo lo que se ve.
5. Junta video + narración en un `.mp4` con ffmpeg.

## Notas importantes

- **La reserva que hace es real** (queda en la base de datos del negocio, con nombre "Cliente Demo") — es intencional, ver el código de confirmación real en pantalla es justo lo que hace creíble el video. Si el prospecto se convierte en cliente, limpiar esa fila de prueba antes de entregarle el sistema.
- Si el servicio de Render estaba dormido, la primera carga puede tardar hasta ~50s — el script ya usa timeouts generosos para eso, no hace falta reintentar a mano.
- Sin `GEMINI_API_KEY` configurada, el video sale igual pero sin narración (silencioso, con los textos superpuestos igual).
- Elige siempre el primer servicio/día/horario disponible — si querés otro, por ahora hay que editar `main.py` (`.service-card`, `.day-chip`, `.time-chip` con `nth=0`).

## Próximas mejoras posibles (no implementadas todavía)
- Elegir servicio/fecha/hora específicos por parámetro en vez de siempre el primero.
- Subtítulos sincronizados con la narración (hoy son solo los textos superpuestos que ya se ven en pantalla).
- Generar en lote una lista de negocios de una vez (ej. desde un CSV) para tener varios videos personalizados listos para outreach.
