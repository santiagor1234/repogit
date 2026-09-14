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
from common.ai import is_live, provider_label  # noqa: E402
from common.inbox import classify, draft_reply  # noqa: E402

DB_PATH = Path(__file__).parent / "leads.db"


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
