"""
Wrapper de IA compartido por las demos.

Prioridad: GEMINI_API_KEY (gratis) -> OPENAI_API_KEY (de pago) -> fallback
por plantilla. Así las demos siempre corren "out of the box" sin necesidad
de configurar nada, y mejoran solas si hay una key disponible.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_provider = None  # "gemini" | "openai" | "none"
_openai_client = None


def _detect_provider() -> str:
    global _provider
    if _provider is not None:
        return _provider
    if os.getenv("GEMINI_API_KEY"):
        _provider = "gemini"
    elif os.getenv("OPENAI_API_KEY"):
        _provider = "openai"
    else:
        _provider = "none"
    return _provider


def is_live() -> bool:
    """True si hay alguna API key configurada y se usará IA real."""
    return _detect_provider() != "none"


def _complete_gemini(prompt: str, system: str, model: str) -> str:
    # API REST directa (en vez del SDK) para no depender de compilar paquetes
    # nativos (grpc/cryptography) que no tienen wheel prearmado en este entorno.
    url = GEMINI_URL.format(model=model)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
    }
    response = requests.post(
        url,
        params={"key": os.getenv("GEMINI_API_KEY")},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _complete_openai(prompt: str, system: str, model: str) -> str:
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = _openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def complete(prompt: str, fallback: str, system: str = "Eres un asistente conciso y útil.", model: str = None) -> str:
    """Devuelve texto generado por IA, o el fallback si no hay ninguna API key configurada."""
    provider = _detect_provider()
    if provider == "none":
        return fallback
    try:
        if provider == "gemini":
            return _complete_gemini(prompt, system, model or "gemini-2.0-flash")
        return _complete_openai(prompt, system, model or "gpt-4o-mini")
    except Exception as exc:  # API caída, rate limit, sin créditos, etc. -> no romper la demo
        print(f"  [aviso] fallo llamando a {provider}, usando fallback: {exc}")
        return fallback
