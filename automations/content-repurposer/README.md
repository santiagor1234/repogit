# Content Repurposer

**El problema que resuelve:** crear contenido corto (Reels/TikTok) a partir de un video/podcast largo toma horas de edición manual para encontrar los mejores momentos. Este demo detecta los momentos más citables de una transcripción y genera hook + caption + hashtags para cada clip.

**Por qué es buen gancho de contenido:** es meta — literalmente se puede usar para generar las ideas del propio contenido del negocio ("automaticé cómo creo mi contenido"). También es un servicio directamente vendible a cualquier creador, coach, o marca que ya genera video/podcast largo.

**Stack:** Python + OpenAI (opcional) + heurística de scoring de texto.

## Correr la demo

```bash
cd automations/content-repurposer
source ../../venv/bin/activate
python main.py
python main.py --clips 6          # más ideas de clips
python main.py --transcript mi_video.txt   # tu propia transcripción
```

Sin `OPENAI_API_KEY`, usa una heurística (palabras clave + números + longitud) para elegir los momentos más citables, y plantillas para el hook/caption. Con la key, usa IA para elegir mejor y redactar de forma más natural.

Salida: JSON en `output/`, y las ideas se agregan automáticamente al final de `content/ideas.md` del proyecto.

## Llevarlo a producción con un cliente

- Reemplazar el `.txt` de transcripción por transcripción automática real: **Whisper API de OpenAI** a partir del audio/video (`client.audio.transcriptions.create`).
- Agregar corte real del video en los timestamps sugeridos (ej. con `ffmpeg`), para entregar los clips ya recortados, no solo la idea.
- Conectar publicación automática (Instagram/TikTok API) para programar los clips directamente.
