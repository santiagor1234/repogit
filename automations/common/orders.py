"""
Catálogo + parseo de pedidos + persistencia, compartido entre la demo
simulada (`pedidos-catalogo`) y el bot de Telegram (`telegram-bot`).

100% basado en reglas (regex sobre el catálogo) — no depende de ninguna
IA. El catálogo controla exactamente qué se puede vender, así que nunca
se "inventa" un producto o un precio.
"""
import re
import sqlite3
from datetime import datetime

CATALOG = [
    {"name": "Hamburguesa", "price": 12000, "aliases": ["hamburguesa", "burger"]},
    {"name": "Perro caliente", "price": 7000, "aliases": ["perro caliente", "perro", "hot dog"]},
    {"name": "Papas fritas", "price": 5000, "aliases": ["papas fritas", "papas"]},
    {"name": "Pizza", "price": 20000, "aliases": ["pizza"]},
    {"name": "Café", "price": 4000, "aliases": ["café", "cafe", "tinto"]},
    {"name": "Empanada", "price": 3000, "aliases": ["empanada"]},
    {"name": "Jugo natural", "price": 5000, "aliases": ["jugo"]},
    {"name": "Sandwich", "price": 8000, "aliases": ["sandwich", "sándwich"]},
    {"name": "Agua", "price": 2500, "aliases": ["agua"]},
    {"name": "Gaseosa", "price": 3500, "aliases": ["gaseosa", "soda", "coca cola", "coca"]},
    {"name": "Torta de chocolate", "price": 6000, "aliases": ["torta de chocolate", "torta", "postre"]},
]

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


def parse_order(text: str, catalog: list = CATALOG):
    """Devuelve la lista de items detectados en `text` (puede estar vacía)."""
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


def format_money(amount: int) -> str:
    return f"${amount:,.0f}".replace(",", ".")


def catalog_listing(catalog: list = CATALOG) -> str:
    return "\n".join(f"- {p['name']}: {format_money(p['price'])}" for p in catalog)


def ensure_orders_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            contact TEXT,
            total INTEGER,
            original_message TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product TEXT,
            quantity INTEGER,
            unit_price INTEGER,
            subtotal INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
    )
    conn.commit()
    return conn


def save_order(conn, client_name, contact, message, items):
    total = sum(i["subtotal"] for i in items)
    cursor = conn.execute(
        "INSERT INTO orders (client_name, contact, total, original_message, created_at) VALUES (?, ?, ?, ?, ?)",
        (client_name, contact, total, message, datetime.now().isoformat()),
    )
    order_id = cursor.lastrowid
    for item in items:
        conn.execute(
            "INSERT INTO order_items (order_id, product, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)",
            (order_id, item["product"], item["quantity"], item["unit_price"], item["subtotal"]),
        )
    conn.commit()
    return order_id, total
