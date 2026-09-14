"""
Demo: AI DM Auto-Responder

Simula la bandeja de entrada (Instagram/WhatsApp) de un negocio. Por cada
mensaje: clasifica la intención (lead / pregunta / spam), genera una
respuesta personalizada al instante, y si es un lead lo guarda en SQLite
para seguimiento.

Uso:
    python main.py
    python main.py --messages otro_archivo.json

En producción, `sample_messages.json` se reemplaza por el webhook real de
Instagram Graph API / WhatsApp Business API (Twilio o Meta directo), y
cada mensaje entrante dispara este mismo pipeline de clasificar -> responder -> loggear.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import complete, is_live, provider_label  # noqa: E402

DB_PATH = Path(__file__).parent / "leads.db"

LEAD_KEYWORDS = ["precio", "cuánto", "cuanto", "cuesta", "costo", "info", "disponible", "reserva", "turno", "cita"]
QUESTION_KEYWORDS = ["horario", "ubicación", "ubicacion", "dónde", "donde", "cuándo", "cuando"]


def classify(text: str) -> str:
    fallback_label = "lead"
    lowered = text.lower()
    if any(k in lowered for k in LEAD_KEYWORDS):
        fallback_label = "lead"
    elif any(k in lowered for k in QUESTION_KEYWORDS):
        fallback_label = "pregunta"
    elif "🙏" in text or "sígueme" in lowered or "siganme" in lowered:
        fallback_label = "spam"
    else:
        fallback_label = "pregunta"

    label = complete(
        prompt=f'Clasifica este mensaje de un DM de red social en una sola palabra: "lead", "pregunta" o "spam".\nMensaje: "{text}"\nResponde solo con la palabra.',
        fallback=fallback_label,
        system="Clasificas mensajes entrantes de un negocio. Respondes solo con una palabra: lead, pregunta o spam.",
    ).strip().lower()

    if label not in {"lead", "pregunta", "spam"}:
        label = fallback_label
    return label


def draft_reply(business: str, sender: str, text: str, label: str) -> str:
    templates = {
        "lead": f"¡Hola {sender.split()[0]}! Gracias por escribirnos a {business} 🙌 Sí, seguimos disponibles. Para darte precio/detalles exactos, ¿nos compartes un poco más sobre lo que necesitas? Un asesor te responde en breve.",
        "pregunta": f"¡Hola {sender.split()[0]}! Gracias por tu mensaje a {business}. Ya te comparto esa información en un momento 🙂",
        "spam": f"¡Gracias por tu apoyo, {sender.split()[0]}! 💛",
    }
    fallback = templates[label]

    return complete(
        prompt=(
            f'Eres el asistente de "{business}" respondiendo DMs de Instagram/WhatsApp.\n'
            f'Mensaje del cliente ({sender}): "{text}"\n'
            f'Categoría: {label}.\n'
            "Escribe una respuesta breve (máx 2 líneas), cálida y natural en español, que avance la conversación."
        ),
        fallback=fallback,
        system=f"Eres el asistente de atención al cliente de {business}. Respondes breve, cálido y natural.",
    )


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            platform TEXT,
            sender TEXT,
            message TEXT,
            reply TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--messages", default="sample_messages.json")
    args = parser.parse_args()

    messages_path = Path(__file__).parent / args.messages
    messages = json.loads(messages_path.read_text())

    conn = ensure_db()
    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, respuestas por plantilla)"
    print(f"AI DM Auto-Responder — {mode}\n{'=' * 60}")

    leads_saved = 0
    for msg in messages:
        label = classify(msg["text"])
        reply = draft_reply(msg["business"], msg["sender"], msg["text"], label)

        print(f"\n[{msg['platform']}] {msg['business']}")
        print(f"  {msg['sender']}: {msg['text']}")
        print(f"  -> clasificado como: {label.upper()}")
        print(f"  Bot: {reply}")

        if label == "lead":
            conn.execute(
                "INSERT INTO leads (business, platform, sender, message, reply, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (msg["business"], msg["platform"], msg["sender"], msg["text"], reply, datetime.now().isoformat()),
            )
            conn.commit()
            leads_saved += 1

    print(f"\n{'=' * 60}")
    print(f"{leads_saved} lead(s) guardado(s) en {DB_PATH.name} (tabla `leads`)")
    conn.close()


if __name__ == "__main__":
    main()
