# Estrategia de venta por redes sociales

Creada 2026-09-14, después de tener el primer producto real funcionando de punta a punta (bot de Telegram + web de reservas + Google Sheets para "Centro medico"). La estrategia se apoya en ese activo: no vendemos una idea, mostramos algo que ya funciona.

## 1. Qué vendemos (la oferta, en una frase)

**"Automatizo la atención de tu negocio — pedidos, citas y respuestas a clientes — para que no pierdas ventas por no contestar a tiempo, y lo pruebas gratis con tu propio negocio antes de pagar un peso."**

El producto concreto hoy: un bot de WhatsApp/Telegram + página de reservas/pedidos + sincronización a Google Sheets, reutilizable para cualquier negocio (ya lo comprobamos con `?business=&phone=&address=` — personalizar toma minutos, no días).

## 2. A quién le vendemos

Nicho amplio a propósito (ver `docs/ofertas.md`), pero el comprador siempre tiene este perfil:

- Negocio local pequeño/mediano que agenda citas o toma pedidos por WhatsApp/Instagram a mano.
- El dueño o alguien del equipo pierde tiempo respondiendo lo mismo una y otra vez, o pierde clientes por no contestar rápido.
- Ejemplos ya cubiertos por las demos: peluquerías, clínicas/consultorios, spas, restaurantes, gimnasios, veterinarias.

## 3. La ventaja injusta: la demo instantánea

Nuestro sistema genérico permite mostrarle a CUALQUIER prospecto, en minutos, cómo se vería su propio negocio funcionando — no un mockup genérico, su nombre, su dirección, su número. Esto tiene que ser el centro de la estrategia de contenido y de outreach: **"te armo una demo con tu negocio en 5 minutos, gratis, sin compromiso."** Nadie más en redes está ofreciendo eso con esa velocidad porque nosotros ya construimos la plantilla reutilizable.

## 4. Pilares de contenido (Instagram/TikTok)

Reels cortos (15-45s), gancho en los primeros 3 segundos, formato vertical. Rotar entre pilares para no aburrir y para probar qué nicho/gancho convierte mejor:

1. **Demo en vivo** — grabar pantalla + celular mostrando el flujo real (cliente escribe → bot responde/agenda/toma pedido → queda en la base de datos/Sheet). El material ya existe: literalmente grabar la sesión que acabamos de probar.
2. **Antes/después** — proceso manual (anotar en un cuaderno, contestar 10 WhatsApps) vs. el mismo proceso automatizado, con tiempo cronometrado en pantalla.
3. **"Te armo tu demo en vivo"** — pedir en los comentarios el nombre de un negocio real (de un seguidor o inventado) y generar la demo personalizada en cámara, mostrando lo rápido que es.
4. **Educativo/contrarian** — por qué la automatización más rentable no es la más compleja (ver `content/ideas.md`, ya hay ejemplos generados), errores comunes al intentar automatizar solo.
5. **Detrás de cámaras / build in public** — mostrar cómo se construyó cada pieza (bot, web, integración a Sheets), incluyendo los tropiezos reales (ej. el error de CORS/CSP que resolvimos hoy es contenido genuino: "el problema que nadie te cuenta al conectar una web a un backend").
6. **Prueba social** — en cuanto haya el primer cliente real, testimonios cortos y métricas concretas (citas agendadas, tiempo ahorrado).

## 5. Embudo (de contenido a cliente)

```
Contenido (Reel) 
   -> CTA: "Escribime 'DEMO' y te armo la tuya gratis"
   -> DM entra al bot de ai-dm-autoresponder/telegram-bot (clasifica el lead automáticamente)
   -> Se genera la demo personalizada (?business=Su+Negocio) y se envía por el mismo chat
   -> Llamada de descubrimiento (agendada con el propio sistema de citas — mismo producto que se vende)
   -> Propuesta con paquete (ver pricing abajo)
   -> Cierre y deploy (días, no semanas, por la plantilla reutilizable)
```

Puntos clave:
- El primer contacto lo puede manejar el propio bot (dogfooding: usamos nuestro producto para vender nuestro producto — buen ángulo de contenido también).
- La llamada de descubrimiento se agenda con la misma web de reservas — otra prueba en vivo del producto.

## 6. Outreach complementario (no depender solo de orgánico)

El contenido orgánico tarda en crecer. Mientras construye tracción, complementar con outbound usando `automations/lead-finder-outreach`:

- Generar listas de negocios locales por nicho/ciudad y mandar un primer mensaje personalizado ofreciendo la demo gratis (mismo gancho que en redes).
- Registrar qué nichos responden mejor — alimenta tanto `docs/ofertas.md` como la decisión futura de si conviene especializarse.

## 7. Oferta y precios (marco inicial, calibrar con cotizaciones reales)

Ahora que hay costos reales de operar esto (Render, dominio eventual, tiempo de soporte), un marco de partida:

- **Setup** (pago único): personalización del bot + web + conexión a Sheets para el negocio del cliente. Cubre el trabajo de una sola vez.
- **Mensualidad**: hosting + mantenimiento + cambios menores + soporte. Cubre el costo continuo (y el upgrade futuro de Render free → paid cuando haya tráfico real, como ya se habló).
- Paquetes por complejidad: básico (solo citas O solo pedidos) vs. completo (ambos + pasarela de pagos, como se está por construir para el caso del restaurante).

_Actualizar esta sección con números reales apenas se cotice al primer cliente — no hay precios de mercado válidos hasta que alguien pague de verdad._

## 8. Qué medir

- Por pieza de contenido: vistas, guardados, comentarios pidiendo demo (la métrica que más importa — intención real, no solo alcance).
- Del embudo: DMs recibidos → demos generadas → llamadas agendadas → clientes cerrados. Si el cuello de botella está en un paso específico, ahí se enfoca el esfuerzo (mejor gancho, mejor demo, mejor propuesta).
- Registrar aprendizajes en `docs/ofertas.md` (qué nicho/oferta resuena) y `content/ideas.md` (qué formato de video funciona).

## 9. Primeros videos concretos (para arrancar ya)

1. "Le escribí a mi propio bot pidiendo una cita y esto pasó" — grabación de pantalla del flujo real de citas, sin edición forzada, mostrando la velocidad real.
2. "Así tomo pedidos sin mover un dedo" — mismo formato con el flujo de pedidos.
3. "Te armo la demo de TU negocio ahora mismo" — formato interactivo pidiendo nombre de negocio en comentarios.
4. "El error que casi arruina mi automatización" — behind the scenes del problema de CSP/CORS resuelto hoy, en tono cercano/educativo, no técnico-denso.
