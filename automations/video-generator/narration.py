"""
Narración por voz para los videos.

Motor principal: Edge TTS (Microsoft) — gratis, sin cuenta, sin límite
diario real. Respaldo: Gemini TTS — solo 10 llamadas gratis POR DÍA
(confirmado con la API: "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
límite 10), así que se reserva para cuando Edge falle por algún motivo.
"""
import asyncio
import base64
import os
import subprocess
import time
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import requests
from dotenv import load_dotenv

load_dotenv()

EDGE_VOICE = "es-CO-GonzaloNeural"
EDGE_RATE = "+15%"  # un poco más rápido que el default, se siente más animado

GEMINI_TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_VOICE = "Puck"  # voz "upbeat" -- solo se usa si Edge TTS falla


def _synthesize_edge(text: str, out_path: Path) -> Path:
    mp3_path = out_path.with_suffix(".mp3")
    communicate = edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE)
    asyncio.run(communicate.save(str(mp3_path)))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-i", str(mp3_path), "-ar", "24000", "-ac", "1", str(out_path)],
        check=True, capture_output=True,
    )
    mp3_path.unlink()
    return out_path


def _synthesize_gemini(text: str, out_path: Path, voice: str = GEMINI_VOICE, model: str = GEMINI_MODEL) -> Path:
    import wave

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en .env para el respaldo de Gemini TTS.")

    url = GEMINI_TTS_URL.format(model=model)
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    last_error = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(5)
        try:
            response = requests.post(url, params={"key": api_key}, json=payload, timeout=60)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            last_error = exc
    else:
        raise last_error

    data = response.json()
    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    audio_bytes = base64.b64decode(part["data"])

    rate = 24000
    mime = part.get("mimeType", "")
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])

    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(audio_bytes)

    return out_path


def synthesize(text: str, out_path: Path) -> Path:
    """Genera un .wav con la narración. Prueba Edge TTS primero (sin límite
    diario); si falla, cae a Gemini TTS (10 llamadas/día gratis)."""
    try:
        return _synthesize_edge(text, out_path)
    except Exception as exc:
        print(f"  [aviso] Edge TTS falló ({exc}), probando Gemini TTS de respaldo...")
        return _synthesize_gemini(text, out_path)
