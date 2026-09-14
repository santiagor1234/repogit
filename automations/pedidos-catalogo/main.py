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

Esta es la versión "de un solo mensaje" (simulada, para ver el resultado
rápido). La versión conversacional real (que recuerda el carrito entre
varios mensajes) está en `automations/telegram-bot/` — ambas comparten
la misma lógica en `common/orders.py`.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.orders import CATALOG, ensure_orders_db, parse_order, save_order, format_money  # noqa: E402

DB_PATH = Path(__file__).parent / "pedidos.db"


def main():
    orders_path = Path(__file__).parent / "sample_orders.json"
    incoming = json.loads(orders_path.read_text(encoding="utf-8"))

    conn = ensure_orders_db(DB_PATH)
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
