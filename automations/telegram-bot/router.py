"""
Router conversacional del bot: decide qué automatización real debe
manejar cada mensaje (pedido / menú de opciones / atención general), y
mantiene el flujo entre varios mensajes usando `sessions.py`.

Separado de `bot.py` (que solo habla con la API de Telegram) para poder
probarlo por consola sin necesitar un bot real — ver `if __name__ ==
"__main__"` al final. Ahí el menú se imprime como texto; en Telegram,
`bot.py` lo convierte en botones reales.
"""
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.inbox import classify, draft_reply  # noqa: E402
from common.orders import ensure_orders_db, format_money, parse_order, save_order  # noqa: E402
from sessions import get_session, reset_session  # noqa: E402

load_dotenv()

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Nuestro negocio")

ORDERS_DB = Path(__file__).resolve().parents[1] / "pedidos-catalogo" / "pedidos.db"

ORDER_TRIGGERS = ["pedido", "pedir", "ordenar"]
MENU_TRIGGERS = ["cita", "agendar", "turno", "reservar hora", "reservar una hora", "agenda",
                 "servicios", "horario", "ubicación", "ubicacion", "menú", "menu", "ayuda"]
GREETING_TRIGGERS = ["hola", "buenas", "buenos días", "buenos dias", "buenas tardes",
                      "buenas noches", "hey", "qué tal", "que tal", "holis", "buen día", "buen dia"]
FINALIZE_TRIGGERS = ["eso es todo", "ya está", "ya esta", "nada más", "nada mas", "es todo",
                      "finalizar", "confirmar pedido", "confirmar", "eso sería todo", "eso seria todo"]
CANCEL_TRIGGERS = ["cancelar", "olvídalo", "olvidalo", "mejor no", "ya no quiero"]

QUANTITY_WORD = re.compile(r"\b(\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\b", re.IGNORECASE)

_orders_conn = None


def _orders_db():
    global _orders_conn
    if _orders_conn is None:
        _orders_conn = ensure_orders_db(ORDERS_DB)
    return _orders_conn


def _contains_any(text, triggers):
    lowered = text.lower()
    return any(t in lowered for t in triggers)


def _looks_like_quantified_order(text):
    """Solo cuenta como intención de pedido "implícita" si además hay una
    cantidad explícita (ej. "2 empanadas") — así "tengo un café" (hablando
    de su propio negocio) no dispara el flujo de pedidos por accidente."""
    items = parse_order(text)
    return bool(items) and bool(QUANTITY_WORD.search(text))


def services_text() -> str:
    return (
        f"🛠️ Servicios de {BUSINESS_NAME}:\n\n"
        "• Consulta / servicio básico — $40.000 (30 min)\n"
        "• Servicio estándar — $70.000 (45 min)\n"
        "• Servicio premium — $120.000 (60 min)\n\n"
        "¿Querés agendar? Tocá 📅 Agendar cita en el menú de arriba."
    )


def hours_text() -> str:
    return (
        f"🕐 Horario de atención de {BUSINESS_NAME}:\n\n"
        "Lunes a viernes: 9:00 am – 5:00 pm\n"
        "Sábados: 9:00 am – 1:00 pm\n"
        "Domingos: cerrado"
    )


def handle_message(chat_id, sender, contact, text):
    """Devuelve un str (respuesta simple) o un dict {"text", "show_menu": True}
    cuando corresponde mostrar el menú de botones."""
    session = get_session(chat_id)

    if session["flow"] and _contains_any(text, CANCEL_TRIGGERS):
        reset_session(chat_id)
        return "Listo, cancelé eso. ¿En qué más te puedo ayudar? 🙂"

    if session["flow"] == "pedido":
        return _handle_pedido(chat_id, sender, contact, text, session)

    if _contains_any(text, GREETING_TRIGGERS):
        return {"text": f"¡Hola {sender}! 👋 Bienvenido a {BUSINESS_NAME}. ¿En qué te ayudamos hoy?", "show_menu": True}

    if _contains_any(text, MENU_TRIGGERS):
        return {"text": "Elegí una opción 👇", "show_menu": True}

    wants_order = _contains_any(text, ORDER_TRIGGERS) or _looks_like_quantified_order(text)
    if wants_order:
        session["flow"] = "pedido"
        return _handle_pedido(chat_id, sender, contact, text, session)

    label = classify(text)
    return draft_reply(BUSINESS_NAME, sender, text, label)


def _pedido_menu_reply(prefix: str) -> str:
    from common.orders import catalog_listing
    return f"{prefix} Este es el menú:\n\n{catalog_listing()}\n\n¿Qué te gustaría pedir?"


def _handle_pedido(chat_id, sender, contact, text, session):
    if _contains_any(text, FINALIZE_TRIGGERS):
        if not session["cart"]:
            reset_session(chat_id)
            return "No alcancé a registrar ningún producto todavía. ¿Me decís qué te gustaría pedir?"
        conn = _orders_db()
        order_id, total = save_order(conn, sender, contact, text, session["cart"])
        summary = "\n".join(f"  {i['quantity']}x {i['product']} ({format_money(i['subtotal'])})" for i in session["cart"])
        reset_session(chat_id)
        return f"¡Gracias {sender}! Tu pedido #{order_id} quedó confirmado:\n{summary}\n\nTotal: {format_money(total)} 🙌"

    items = parse_order(text)
    if not items:
        return _pedido_menu_reply("No identifiqué ningún producto ahí.")

    session["cart"].extend(items)
    total = sum(i["subtotal"] for i in session["cart"])
    added = "\n".join(f"  {i['quantity']}x {i['product']} ({format_money(i['subtotal'])})" for i in items)
    return (
        f"¡Agregado!\n{added}\n\n"
        f"Tu pedido hasta ahora: {format_money(total)} total.\n"
        "¿Algo más? Si ya está, escribí 'eso es todo' para confirmar."
    )


if __name__ == "__main__":
    # Probar el router por consola, sin necesitar Telegram (el menú se
    # imprime como lista de opciones en vez de botones reales).
    print("Router de prueba (sin Telegram). Escribí mensajes como si fueras un cliente. Ctrl+C para salir.\n")
    chat_id = "consola"
    while True:
        text = input("Vos: ")
        reply = handle_message(chat_id, "Tester", "consola", text)
        if isinstance(reply, dict):
            print(f"Bot: {reply['text']}")
            if reply.get("show_menu"):
                print("     [📅 Agendar cita] [🛠️ Servicios] [🕐 Horario] [📍 Ubicación]")
        else:
            print(f"Bot: {reply}")
        print()
