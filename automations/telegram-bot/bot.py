"""
Bot de Telegram — versión real (no simulada) de las automatizaciones de
atención, pedidos y agendamiento.

Usa `router.py` (que mantiene memoria de conversación por chat) conectado
a un bot de Telegram real vía long polling — el bot pregunta por mensajes
nuevos cada cierto tiempo, así que no necesita servidor público ni
webhook. Ideal para probar desde tu celular antes de portar esto a
WhatsApp Business API.

Setup:
    1. En Telegram, habla con @BotFather -> /newbot -> seguí las instrucciones.
    2. Copiá el token que te da y pegalo en .env como TELEGRAM_BOT_TOKEN=...
    3. python bot.py
    4. Buscá tu bot en Telegram (el username que le pusiste) y escribile /start.

Ctrl+C para detenerlo.
"""
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from router import handle_message, hours_text, services_text  # noqa: E402
from sessions import reset_session  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import is_live, provider_label  # noqa: E402

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Nuestro negocio")
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "Cra 15 #93-47, Bogotá")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE", "+57 300 000 0000")

# URL pública de automations/booking-api ya desplegada (ej. Render). La propia API
# sirve la web de reservas en "/" — un Claude Artifact NO puede llamar a una API
# externa (su CSP bloquea fetch() a cualquier dominio fuera de unos pocos CDNs), así
# que la web y la API tienen que vivir en el mismo origen.
BOOKING_API_URL = os.getenv("BOOKING_API_URL")

if BOOKING_API_URL:
    BOOKING_BASE_URL = BOOKING_API_URL.rstrip("/") + "/"
else:
    # Sin API desplegada todavía: cae al artifact de Claude, que se muestra en
    # "vista previa" (no guarda nada real, pero sirve para mostrar el diseño).
    BOOKING_BASE_URL = "https://claude.ai/code/artifact/7607c251-5762-4c64-9c43-885a0ee90c26"

BOOKING_URL = (
    f"{BOOKING_BASE_URL}?business={quote(BUSINESS_NAME)}"
    f"&phone={quote(BUSINESS_PHONE)}&address={quote(BUSINESS_ADDRESS)}"
)
MAPS_URL = f"https://www.google.com/maps/search/?api=1&query={quote(BUSINESS_ADDRESS)}"

MENU_KEYBOARD = {
    "inline_keyboard": [
        [{"text": "📅 Agendar cita", "url": BOOKING_URL}],
        [{"text": "🛠️ Servicios", "callback_data": "servicios"},
         {"text": "🕐 Horario", "callback_data": "horario"}],
        [{"text": "📍 Ubicación", "url": MAPS_URL}],
    ]
}

WELCOME = f"¡Hola! 👋 Bienvenido a {BUSINESS_NAME}. ¿En qué te ayudamos hoy?"


def get_updates(offset=None):
    params = {"timeout": 30, "allowed_updates": '["message","callback_query"]'}
    if offset is not None:
        params["offset"] = offset
    response = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40)
    response.raise_for_status()
    return response.json()["result"]


def send_message(chat_id, text, with_menu=False):
    payload = {"chat_id": chat_id, "text": text}
    if with_menu:
        payload["reply_markup"] = MENU_KEYBOARD
    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=15)


def answer_callback(callback_query_id):
    requests.post(f"{API_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id}, timeout=15)


def handle_update(update):
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq["data"]
        answer_callback(cq["id"])

        print(f"[botón] {data}")
        if data == "servicios":
            send_message(chat_id, services_text())
        elif data == "horario":
            send_message(chat_id, hours_text())
        return

    message = update.get("message")
    if not message or "text" not in message:
        return

    chat_id = message["chat"]["id"]
    sender = message["from"].get("first_name", "Cliente")
    contact = message["from"].get("username") or f"telegram:{chat_id}"
    text = message["text"]

    print(f"{sender}: {text}")

    if text.strip() == "/start":
        reset_session(chat_id)
        print(f"  Bot: {WELCOME}\n     [menú]\n")
        send_message(chat_id, WELCOME, with_menu=True)
        return

    reply = handle_message(chat_id, sender, contact, text)
    if isinstance(reply, dict):
        print(f"  Bot: {reply['text']}\n     [menú]\n")
        send_message(chat_id, reply["text"], with_menu=reply.get("show_menu", False))
    else:
        print(f"  Bot: {reply}\n")
        send_message(chat_id, reply)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en .env. Mirá el README.md de esta carpeta para crear el bot con @BotFather.")
        return

    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, respuestas por plantilla)"
    print(f"Bot de Telegram — {mode}")
    print(f"Negocio: {BUSINESS_NAME}  |  Reservas: {BOOKING_URL}")
    print("Buscá tu bot en Telegram y escribile /start. Ctrl+C para detener.\n")

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
            handle_update(update)


if __name__ == "__main__":
    main()
