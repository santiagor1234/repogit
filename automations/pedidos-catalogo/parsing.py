"""Extrae productos + cantidades de un mensaje en lenguaje natural.

100% basado en reglas (regex sobre el catálogo) — no depende de ninguna
IA. El catálogo controla exactamente qué se puede vender, así que nunca
se inventa un producto que no existe.
"""
import re

NUMBER_WORDS = {
    "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
}


def _parse_quantity(token):
    if token is None:
        return 1
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return NUMBER_WORDS.get(token, 1)


def parse_order(text: str, catalog: list):
    lowered = text.lower()
    number_pattern = "|".join(NUMBER_WORDS.keys())
    items = []

    for product in catalog:
        for alias in product["aliases"]:
            pattern = re.compile(
                rf"(?:(\d+|{number_pattern})\s+)?{re.escape(alias)}s?\b",
                re.IGNORECASE,
            )
            match = pattern.search(lowered)
            if match:
                quantity = _parse_quantity(match.group(1))
                items.append(
                    {
                        "product": product["name"],
                        "unit_price": product["price"],
                        "quantity": quantity,
                        "subtotal": quantity * product["price"],
                    }
                )
                break  # ya encontramos este producto, seguir con el siguiente del catálogo

    return items
