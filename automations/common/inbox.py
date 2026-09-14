"""
Lógica compartida para responder mensajes entrantes de un negocio (DMs).

La usan tanto la demo simulada (`ai-dm-autoresponder`, que lee de un JSON)
como el bot real de Telegram (`telegram-bot`) — así ambos se comportan
exactamente igual y no hay que mantener la lógica en dos lugares.
"""
from .ai import complete

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
