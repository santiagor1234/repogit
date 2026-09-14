"""
Bot de Telegram — versión real (no simulada) del AI DM Auto-Responder.

Usa la misma lógica de clasificación + respuesta de `common/inbox.py`,
pero conectada a un bot de Telegram de verdad vía long polling (el bot
pregunta por mensajes nuevos cada cierto tiempo, así que no necesita un
servidor público ni webhook — ideal para probar desde tu celular ahora
mismo, antes de portar esto a WhatsApp Business API).

Setup:
    1. En Telegram, habla con @BotFather -> /newbot -> seguí las instrucciones.
    2. Copiá el token que te da y pegalo en .env como TELEGRAM_BOT_TOKEN=...
    3. (Opcional) Poné BUSINESS_NAME=Tu Negocio en .env.
    4. python bot.py
    5. Buscá tu bot en Telegram (el username que le pusiste) y escribile.

Ctrl+C para detenerlo.
"""
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import is_live, provider_label  # noqa: E402
from common.inbox import classify, draft_reply  # noqa: E402

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Mi Negocio")
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


def get_updates(offset=None):
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    response = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40)
    response.raise_for_status()
    return response.json()["result"]


def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en .env. Mirá el README.md de esta carpeta para crear el bot con @BotFather.")
        return

    conn = ensure_db()
    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, respuestas por plantilla)"
    print(f"Bot de Telegram — {mode}")
    print(f"Negocio simulado: {BUSINESS_NAME}")
    print("Buscá tu bot en Telegram y escribile. Ctrl+C para detener.\n")

    offset = None
    while True:
        try:
            updates = get_updates(offset)
        except requests.exceptions.RequestException as exc:
            print(f"  [aviso] error consultando Telegram, reintentando: {exc}")
            time.sleep(3)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message or "text" not in message:
                continue

            chat_id = message["chat"]["id"]
            sender = message["from"].get("first_name", "Cliente")
            text = message["text"]

            print(f"{sender}: {text}")
            label = classify(text)
            reply = draft_reply(BUSINESS_NAME, sender, text, label)
            print(f"  -> {label.upper()}")
            print(f"  Bot: {reply}\n")

            send_message(chat_id, reply)

            if label == "lead":
                conn.execute(
                    "INSERT INTO leads (business, platform, sender, message, reply, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (BUSINESS_NAME, "Telegram", sender, text, reply, datetime.now().isoformat()),
                )
                conn.commit()


if __name__ == "__main__":
    main()
