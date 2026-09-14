"""
Router conversacional del bot: decide qué automatización real debe
manejar cada mensaje (pedido / cita / atención general), y mantiene el
flujo entre varios mensajes usando `sessions.py`.

Separado de `bot.py` (que solo habla con la API de Telegram) para poder
probarlo por consola sin necesitar un bot real — ver `if __name__ ==
"__main__"` al final.
"""
import re
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.appointments import (  # noqa: E402
    book_slot,
    ensure_appointments_db,
    find_best_slot,
    format_date_es,
    parse_preferred_date,
    parse_preferred_time,
)
from common.inbox import classify, draft_reply  # noqa: E402
from common.orders import catalog_listing, ensure_orders_db, format_money, parse_order, save_order  # noqa: E402
from sessions import get_session, reset_session  # noqa: E402

ORDERS_DB = Path(__file__).resolve().parents[1] / "pedidos-catalogo" / "pedidos.db"
APPOINTMENTS_DB = Path(__file__).resolve().parents[1] / "citas-booking" / "citas.db"

ORDER_TRIGGERS = ["pedido", "pedir", "ordenar", "menú", "menu"]
APPOINTMENT_TRIGGERS = ["cita", "agendar", "turno", "reservar hora", "reservar una hora", "agenda"]
FINALIZE_TRIGGERS = ["eso es todo", "ya está", "ya esta", "nada más", "nada mas", "es todo",
                      "finalizar", "confirmar pedido", "confirmar", "eso sería todo", "eso seria todo"]
CANCEL_TRIGGERS = ["cancelar", "olvídalo", "olvidalo", "mejor no", "ya no quiero"]

QUANTITY_WORD = re.compile(r"\b(\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\b", re.IGNORECASE)

_orders_conn = None
_appointments_conn = None


def _orders_db():
    global _orders_conn
    if _orders_conn is None:
        _orders_conn = ensure_orders_db(ORDERS_DB)
    return _orders_conn


def _appointments_db():
    global _appointments_conn
    if _appointments_conn is None:
        _appointments_conn = ensure_appointments_db(APPOINTMENTS_DB)
    return _appointments_conn


def _contains_any(text, triggers):
    lowered = text.lower()
    return any(t in lowered for t in triggers)


def _looks_like_quantified_order(text):
    """Solo cuenta como intención de pedido "implícita" si además hay una
    cantidad explícita (ej. "2 empanadas") — así "tengo un café" (hablando
    de su propio negocio) no dispara el flujo de pedidos por accidente."""
    items = parse_order(text)
    return bool(items) and bool(QUANTITY_WORD.search(text))


def handle_message(chat_id, sender, contact, text) -> str:
    session = get_session(chat_id)

    if session["flow"] and _contains_any(text, CANCEL_TRIGGERS):
        reset_session(chat_id)
        return "Listo, cancelé eso. ¿En qué más te puedo ayudar? 🙂"

    if session["flow"] == "pedido":
        return _handle_pedido(chat_id, sender, contact, text, session)

    if session["flow"] == "cita":
        return _handle_cita(chat_id, sender, contact, text, session)

    wants_order = _contains_any(text, ORDER_TRIGGERS) or _looks_like_quantified_order(text)
    wants_appointment = _contains_any(text, APPOINTMENT_TRIGGERS)

    if wants_order and not wants_appointment:
        session["flow"] = "pedido"
        return _handle_pedido(chat_id, sender, contact, text, session)

    if wants_appointment and not wants_order:
        session["flow"] = "cita"
        return _handle_cita(chat_id, sender, contact, text, session)

    label = classify(text)
    return draft_reply("Nuestro negocio", sender, text, label)


def _pedido_menu_reply(prefix: str) -> str:
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


def _handle_cita(chat_id, sender, contact, text, session):
    preferred_date = parse_preferred_date(text, date.today())
    preferred_time = parse_preferred_time(text)
    if preferred_date:
        session["preferred_date"] = preferred_date
    if preferred_time:
        session["preferred_time"] = preferred_time

    if session["preferred_date"] is None:
        return f"¡Hola {sender}! Claro, te ayudo a agendar. ¿Qué día te gustaría la cita?"

    conn = _appointments_db()
    slot = find_best_slot(conn, session["preferred_date"], session["preferred_time"])
    if slot is None:
        session["preferred_date"] = None
        session["preferred_time"] = None
        return "No encontramos disponibilidad para esa fecha. ¿Tenés otro día en mente?"

    slot_id, slot_date, slot_time = slot
    book_slot(conn, slot, sender, contact, text)
    d = date.fromisoformat(slot_date)
    reset_session(chat_id)
    return f"¡Listo {sender}! Quedaste agendado para el {format_date_es(d)} a las {slot_time}. Te esperamos 🙌"


if __name__ == "__main__":
    # Probar el router por consola, sin necesitar Telegram.
    print("Router de prueba (sin Telegram). Escribí mensajes como si fueras un cliente. Ctrl+C para salir.\n")
    chat_id = "consola"
    while True:
        text = input("Vos: ")
        print(f"Bot: {handle_message(chat_id, 'Tester', 'consola', text)}\n")
