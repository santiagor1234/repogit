# Toma de Pedidos Automática

**El problema que resuelve:** tomar pedidos por WhatsApp/Instagram a mano (leer, anotar, calcular el total, confirmar) es lento y se presta a errores. Este demo lee el pedido en lenguaje natural, identifica productos y cantidades del catálogo, calcula el total y confirma automáticamente.

**Por qué es buen gancho de venta:** aplica directo a cualquier negocio que vende por catálogo/menú (restaurantes, cafeterías, tiendas, panaderías...). El "wow": el cliente escribe como le sale natural ("2 empanadas y un jugo") y el pedido queda registrado y confirmado al instante, con el total calculado.

**Importante — esta automatización es 100% basada en reglas, no usa IA.** El catálogo (`common/orders.py`) controla exactamente qué se puede vender y a qué precio, así que nunca se "inventa" un producto o un precio equivocado — algo que sí podría pasar con una IA generativa sin control. Tampoco tiene costo por mensaje.

**Stack:** Python (regex sobre catálogo) + SQLite.

## Correr la demo

```bash
cd automations/pedidos-catalogo
source ../../venv/bin/activate
python main.py
```

Prueba también cambiando `sample_orders.json` o el catálogo (`CATALOG` en `common/orders.py`) para otro tipo de negocio (el patrón de aliases + precio es genérico, no depende de un rubro).

## Probarlo con un chat real (no simulado)

Ver `automations/telegram-bot/` — mantiene el carrito entre varios mensajes (podés pedir en dos mensajes distintos y el bot lo suma), a diferencia de este demo que procesa cada mensaje de una sola vez.

## Llevarlo a producción con un cliente

- Reemplazar `sample_orders.json` por el webhook real de WhatsApp/Instagram.
- Reemplazar el catálogo por la tabla `products` real del negocio (o sincronizarla con su sistema de inventario/POS).
- Agregar confirmación de pago (link de pago automático) y notificación al negocio cuando entra un pedido nuevo.
- Si el mensaje no matchea ningún producto (como el último ejemplo, que solo pregunta por domicilio), el bot avisa que no identificó productos en vez de inventar un pedido — ese es el comportamiento esperado, no un bug.
