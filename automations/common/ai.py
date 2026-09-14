"""
Wrapper de IA compartido por las demos.

Si hay OPENAI_API_KEY en el entorno (.env), usa el modelo real.
Si no, cae en el `fallback` que reciba cada llamada, para que las
demos siempre corran "out of the box" sin necesidad de configurar nada.
"""
import os

from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI

    _client = OpenAI(api_key=api_key)
    return _client


def is_live() -> bool:
    """True si hay una API key configurada y se usará IA real."""
    return _get_client() is not None


def complete(prompt: str, fallback: str, system: str = "Eres un asistente conciso y útil.", model: str = "gpt-4o-mini") -> str:
    """Devuelve texto generado por IA, o el fallback si no hay API key configurada."""
    client = _get_client()
    if client is None:
        return fallback
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # API caída, rate limit, etc. -> no romper la demo
        print(f"  [aviso] fallo llamando a OpenAI, usando fallback: {exc}")
        return fallback
