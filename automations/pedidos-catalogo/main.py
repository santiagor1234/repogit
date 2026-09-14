"""
Demo: Toma de pedidos automática

Lee mensajes de clientes pidiendo productos en lenguaje natural, identifica
qué productos del catálogo pidieron (con cantidad), calcula el total,
guarda el pedido y confirma automáticamente — sin que nadie tenga que
tipear el pedido a mano en ningún sistema.

100% basado en reglas: el catálogo controla exactamente qué se puede
vender, así que nunca se "inventa" un producto o precio. No depende de
ninguna IA ni tiene costo por mensaje.

Uso:
    python main.py

En producción, `sample_orders.json` se reemplaza por el webhook real de
WhatsApp/Instagram, y `catalog.py` se sincroniza con el inventario real
del negocio (o se lee directo de una tabla `products` en la base de datos).
"""
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from catalog import CATALOG  # noqa: E402
from parsing import parse_order  # noqa: E402

DB_PATH = Path(__file__).parent / "pedidos.db"


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
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


def format_money(amount: int) -> str:
    return f"${amount:,.0f}".replace(",", ".")


def main():
    orders_path = Path(__file__).parent / "sample_orders.json"
    incoming = json.loads(orders_path.read_text(encoding="utf-8"))

    conn = ensure_db()
    print("Toma de pedidos automática (100% basado en reglas, sin IA)")
    print(f"Catálogo: {', '.join(p['name'] for p in CATALOG)}")
    print("=" * 60)

    orders_saved = 0
    for req in incoming:
        print(f"\n{req['client_name']} ({req['contact']}): \"{req['text']}\"")
        items = parse_order(req["text"], CATALOG)

        if not items:
            print("  Bot: ¡Gracias por escribirnos! No identificamos productos específicos en tu mensaje, ya te contactamos para tomar tu pedido.")
            continue

        order_id, total = save_order(conn, req["client_name"], req["contact"], req["text"], items)
        orders_saved += 1

        print(f"  Bot: ¡Gracias {req['client_name'].split()[0]}! Tu pedido #{order_id} quedó registrado:")
        for item in items:
            print(f"       {item['quantity']}x {item['product']} = {format_money(item['subtotal'])}")
        print(f"       Total: {format_money(total)}")

    print(f"\n{'=' * 60}")
    print(f"{orders_saved} pedido(s) guardado(s) en {DB_PATH.name} (tablas `orders` / `order_items`)")
    conn.close()


if __name__ == "__main__":
    main()
