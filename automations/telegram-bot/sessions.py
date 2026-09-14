"""
Estado de conversación en memoria, por chat de Telegram.

Sin esto, cada mensaje se trata aislado (lo que causaba que "2 perros y
una hamburguesa" se clasificara como spam en vez de reconocerse como
continuación de un pedido). Con sesión, el bot recuerda en qué flujo está
(pedido / cita / ninguno) y qué se lleva acumulado hasta ahora.

En memoria (se pierde si reiniciás el bot) — para producción real se
persistiría en SQLite/Redis, pero para probar el flujo alcanza y sobra.
"""

_sessions = {}


def get_session(chat_id):
    return _sessions.setdefault(
        chat_id,
        {
            "flow": None,  # None | "pedido" | "cita"
            "cart": [],
            "preferred_date": None,
            "preferred_time": None,
        },
    )


def reset_session(chat_id):
    _sessions[chat_id] = {
        "flow": None,
        "cart": [],
        "preferred_date": None,
        "preferred_time": None,
    }
