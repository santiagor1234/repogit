"""
Estado de conversación en memoria, por chat de Telegram.

Sin esto, cada mensaje se trata aislado (lo que causaba que "2 perros y
una hamburguesa" se clasificara como spam en vez de reconocerse como
continuación de un pedido). Con sesión, el bot recuerda si está en medio
de un pedido y qué se lleva acumulado hasta ahora. (Agendar citas ya no
usa sesión: va directo al botón que abre la web de reservas.)

En memoria (se pierde si reiniciás el bot) — para producción real se
persistiría en SQLite/Redis, pero para probar el flujo alcanza y sobra.
"""

_sessions = {}


def get_session(chat_id):
    return _sessions.setdefault(
        chat_id,
        {
            "flow": None,  # None | "pedido"
            "cart": [],
        },
    )


def reset_session(chat_id):
    _sessions[chat_id] = {
        "flow": None,
        "cart": [],
    }
