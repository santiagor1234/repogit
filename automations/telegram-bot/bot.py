"""
Bot de Telegram — versión real (no simulada) de las automatizaciones de
atención, pedidos y citas.

Usa `router.py` (que mantiene memoria de conversación por chat) conectado
a un bot de Telegram real vía long polling — el bot pregunta por mensajes
nuevos cada cierto tiempo, así que no necesita servidor público ni
webhook. Ideal para probar desde tu celular antes de portar esto a
WhatsApp Business API.

Setup:
    1. En Telegram, habla con @BotFather -> /newbot -> seguí las instrucciones.
    2. Copiá el token que te da y pegalo en .env como TELEGRAM_BOT_TOKEN=...
    3. python bot.py
    4. Buscá tu bot en Telegram (el username que le pusiste) y escribile.

Ctrl+C para detenerlo.
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from router import handle_message  # noqa: E402
from sessions import reset_session  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import is_live, provider_label  # noqa: E402

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

WELCOME = (
    "¡Hola! 👋 Puedo ayudarte a:\n"
    "  • Hacer un pedido (escribí 'quiero hacer un pedido' o directo lo que querés, ej. '2 empanadas y un café')\n"
    "  • Agendar una cita (escribí 'quiero agendar una cita')\n"
    "  • Responder cualquier otra pregunta sobre el negocio\n\n"
    "¿En qué te ayudo?"
)


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

    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, respuestas por plantilla)"
    print(f"Bot de Telegram — {mode}")
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
            contact = message["from"].get("username") or f"telegram:{chat_id}"
            text = message["text"]

            print(f"{sender}: {text}")

            if text.strip() == "/start":
                reset_session(chat_id)
                reply = WELCOME
            else:
                reply = handle_message(chat_id, sender, contact, text)

            print(f"  Bot: {reply}\n")
            send_message(chat_id, reply)


if __name__ == "__main__":
    main()
