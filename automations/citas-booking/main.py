"""
Demo: Agendamiento de citas automático

Lee mensajes de clientes pidiendo cita, entiende la fecha/hora preferida
(lenguaje natural en español), busca el espacio disponible más cercano en
el calendario y agenda automáticamente — sin que nadie del negocio toque
un calendario a mano.

100% basado en reglas: no depende de ninguna IA para funcionar, así que es
determinístico y no tiene costo por mensaje. Ideal para un proceso crítico
como agendar (mejor que falle claro a que "alucine" un horario).

Uso:
    python main.py

Esta es la versión "de un solo mensaje" (simulada, para ver el resultado
rápido). La versión conversacional real (que recuerda la preferencia de
fecha/hora entre varios mensajes) está en `automations/telegram-bot/` —
ambas comparten la misma lógica en `common/appointments.py`.
"""
import json
from datetime import date
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.appointments import (  # noqa: E402
    book_slot,
    ensure_appointments_db,
    find_best_slot,
    format_date_es,
    parse_preferred_date,
    parse_preferred_time,
)

DB_PATH = Path(__file__).parent / "citas.db"


def main():
    requests_path = Path(__file__).parent / "sample_requests.json"
    requests_data = json.loads(requests_path.read_text(encoding="utf-8"))

    conn = ensure_appointments_db(DB_PATH)
    print("Agendamiento de citas automático (100% basado en reglas, sin IA)")
    print("=" * 60)

    booked = 0
    for req in requests_data:
        preferred_date = parse_preferred_date(req["text"], date.today())
        preferred_time = parse_preferred_time(req["text"])

        print(f"\n{req['client_name']} ({req['contact']}): \"{req['text']}\"")
        detected = []
        if preferred_date:
            detected.append(format_date_es(preferred_date))
        if preferred_time:
            detected.append(preferred_time.strftime("%H:%M"))
        print(f"  -> preferencia detectada: {', '.join(detected) if detected else 'sin preferencia (primer espacio disponible)'}")

        slot = find_best_slot(conn, preferred_date, preferred_time)
        if slot is None:
            print("  Bot: Lo siento, no encontramos disponibilidad por ahora. Te contactamos apenas se libere un espacio.")
            continue

        slot_id, slot_date, slot_time = slot
        book_slot(conn, slot, req["client_name"], req["contact"], req["text"])
        booked += 1
        d = date.fromisoformat(slot_date)
        print(f"  Bot: ¡Listo {req['client_name'].split()[0]}! Quedaste agendado para el {format_date_es(d)} a las {slot_time}. Te esperamos 🙌")

    print(f"\n{'=' * 60}")
    print(f"{booked} cita(s) agendada(s) en {DB_PATH.name} (tabla `appointments`)")
    conn.close()


if __name__ == "__main__":
    main()
