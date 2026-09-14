"""
Demo: Content Repurposer

Toma la transcripción de un video/podcast largo y la convierte en ideas de
clips cortos: detecta los momentos más "citables", y para cada uno genera
un hook (primeros 3 segundos), un caption y hashtags — listos para grabar
o recortar. Al final, agrega las ideas a `content/ideas.md` del proyecto.

Uso:
    python main.py
    python main.py --transcript otro_archivo.txt --clips 5

En producción, la transcripción se genera automáticamente con la API de
Whisper (OpenAI) a partir del audio/video real, en vez de venir de un
.txt de muestra — el resto del pipeline (detectar momentos, generar
hooks/captions) es igual.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import complete, is_live, provider_label  # noqa: E402

OUTPUT_DIR = Path(__file__).parent / "output"
IDEAS_MD = Path(__file__).resolve().parents[2] / "content" / "ideas.md"

WORDS_PER_MINUTE = 150

KEYWORDS = [
    "nadie", "error", "secreto", "nunca", "siempre", "dato", "consejo",
    "verdadero", "no necesitas", "aprendí", "gigante", "oro", "clave",
]


def split_sentences(text: str):
    text = " ".join(text.split())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def score_sentence(sentence: str) -> int:
    lowered = sentence.lower()
    score = sum(2 for k in KEYWORDS if k in lowered)
    if any(ch.isdigit() for ch in sentence):
        score += 2
    if "%" in sentence:
        score += 1
    word_count = len(sentence.split())
    if 8 <= word_count <= 28:
        score += 1
    return score


def estimate_timestamps(sentences):
    """Aproxima el timestamp de cada oración según cantidad de palabras acumuladas."""
    timestamps = []
    cumulative_words = 0
    for s in sentences:
        seconds = int((cumulative_words / WORDS_PER_MINUTE) * 60)
        timestamps.append(f"{seconds // 60:02d}:{seconds % 60:02d}")
        cumulative_words += len(s.split())
    return timestamps


def pick_top_moments(sentences, timestamps, n):
    scored = [(score_sentence(s), i) for i, s in enumerate(sentences)]
    scored.sort(key=lambda x: x[0], reverse=True)
    top_indices = sorted(i for _, i in scored[:n])
    return [(timestamps[i], sentences[i]) for i in top_indices]


def generate_clip_package(quote: str):
    if len(quote) <= 60:
        fallback_hook = quote
    else:
        fallback_hook = quote[:57].rsplit(" ", 1)[0] + "..."
    fallback_caption = f'"{quote}" — Guardá esto si estás automatizando tu negocio 👇'
    fallback_hashtags = ["#automatizacion", "#emprendimiento", "#ia", "#negociosdigitales", "#productividad"]

    raw = complete(
        prompt=(
            f'Frase de un video sobre automatización de negocios: "{quote}"\n\n'
            "Genera, en formato JSON exacto (sin texto extra), estas 3 claves:\n"
            '{"hook": "línea de gancho para los primeros 3 segundos del video", '
            '"caption": "caption para Instagram/TikTok de 2-3 líneas", '
            '"hashtags": ["5 hashtags relevantes en español, sin espacios, con #"]}'
        ),
        fallback=json.dumps({"hook": fallback_hook, "caption": fallback_caption, "hashtags": fallback_hashtags}),
        system="Eres un experto en contenido corto para redes sobre automatización y negocios. Respondes solo JSON válido.",
    )
    try:
        data = json.loads(raw)
        assert {"hook", "caption", "hashtags"} <= data.keys()
        return data
    except Exception:
        return {"hook": fallback_hook, "caption": fallback_caption, "hashtags": fallback_hashtags}


def append_to_content_ideas(clips):
    if not IDEAS_MD.exists():
        return
    lines = ["", f"## Generado automáticamente — {datetime.now().strftime('%Y-%m-%d %H:%M')} (content-repurposer)", ""]
    for clip in clips:
        caption = " ".join(clip["caption"].split())
        lines.append(f"- **[{clip['timestamp']}] {clip['hook']}**")
        lines.append(f"  - Cita: \"{clip['quote']}\"")
        lines.append(f"  - Caption: {caption}")
        lines.append(f"  - Hashtags: {' '.join(clip['hashtags'])}")
    with open(IDEAS_MD, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", default="sample_transcript.txt")
    parser.add_argument("--clips", type=int, default=4)
    args = parser.parse_args()

    transcript_path = Path(__file__).parent / args.transcript
    text = transcript_path.read_text(encoding="utf-8")

    sentences = split_sentences(text)
    timestamps = estimate_timestamps(sentences)
    moments = pick_top_moments(sentences, timestamps, args.clips)

    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, hooks/captions por plantilla)"
    print(f"Content Repurposer — {mode}")
    print(f"Transcript: {transcript_path.name} ({len(sentences)} oraciones) -> {len(moments)} clips sugeridos")
    print("=" * 60)

    clips = []
    for timestamp, quote in moments:
        package = generate_clip_package(quote)
        clip = {"timestamp": timestamp, "quote": quote, **package}
        clips.append(clip)

        print(f"\n[{timestamp}] HOOK: {clip['hook']}")
        print(f"  Cita: \"{quote}\"")
        print(f"  Caption: {clip['caption']}")
        print(f"  Hashtags: {' '.join(clip['hashtags'])}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"clips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8")

    append_to_content_ideas(clips)

    print(f"\n{'=' * 60}")
    print(f"{len(clips)} ideas de clips guardadas en {out_path.relative_to(Path(__file__).parent)}")
    print(f"y agregadas a {IDEAS_MD.relative_to(Path(__file__).resolve().parents[2])}")


if __name__ == "__main__":
    main()
