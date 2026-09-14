"""Narración por voz con Gemini TTS (texto -> audio)."""
import base64
import os
import time
import wave
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Kore"


def synthesize(text: str, out_path: Path, voice: str = DEFAULT_VOICE, model: str = DEFAULT_MODEL) -> Path:
    """Genera un .wav con la narración. Lanza excepción si no hay GEMINI_API_KEY o falla la API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en .env para generar narración.")

    url = TTS_URL.format(model=model)
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
            time.sleep(2)
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

    # mimeType típico: "audio/L16;codec=pcm;rate=24000" -> PCM 16-bit mono sin encabezado WAV
    rate = 24000
    mime = part.get("mimeType", "")
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])

    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(rate)
        wav_file.writeframes(audio_bytes)

    return out_path
