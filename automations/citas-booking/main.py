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

En producción, `sample_requests.json` se reemplaza por el webhook real de
WhatsApp/Instagram, y el calendario (`slots`) se sincroniza con Google
Calendar/Calendly en vez de vivir solo en SQLite.
"""
import json
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from parsing import parse_preferred_date, parse_preferred_time, format_date_es  # noqa: E402

DB_PATH = Path(__file__).parent / "citas.db"
BUSINESS_HOURS = range(9, 17)  # 9am a 4pm (última cita 16:00)
DAYS_AHEAD_TO_SEED = 14


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            available INTEGER DEFAULT 1
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            contact TEXT,
            date TEXT,
            time TEXT,
            original_message TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
    if count == 0:
        seed_slots(conn)
    return conn


def seed_slots(conn):
    today = date.today()
    for i in range(1, DAYS_AHEAD_TO_SEED + 1):
        d = today + timedelta(days=i)
        if d.weekday() >= 5:  # sábado/domingo: cerrado
            continue
        for hour in BUSINESS_HOURS:
            conn.execute(
                "INSERT INTO slots (date, time, available) VALUES (?, ?, 1)",
                (d.isoformat(), f"{hour:02d}:00"),
            )
    conn.commit()


def find_best_slot(conn, preferred_date, preferred_time):
    query = "SELECT id, date, time FROM slots WHERE available = 1"
    params = []
    if preferred_date:
        query += " AND date >= ?"
        params.append(preferred_date.isoformat())
    query += " ORDER BY date, time"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        return None

    if preferred_date:
        same_day = [r for r in rows if r[1] == preferred_date.isoformat()]
        candidates = same_day if same_day else rows
    else:
        candidates = rows

    if preferred_time:
        target_minutes = preferred_time.hour * 60 + preferred_time.minute
        candidates = sorted(
            candidates,
            key=lambda r: abs(int(r[2][:2]) * 60 - target_minutes),
        )

    return candidates[0]


def book_slot(conn, slot, client_name, contact, message):
    slot_id, slot_date, slot_time = slot
    conn.execute("UPDATE slots SET available = 0 WHERE id = ?", (slot_id,))
    conn.execute(
        "INSERT INTO appointments (client_name, contact, date, time, original_message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (client_name, contact, slot_date, slot_time, message, datetime.now().isoformat()),
    )
    conn.commit()


def main():
    requests_path = Path(__file__).parent / "sample_requests.json"
    requests_data = json.loads(requests_path.read_text(encoding="utf-8"))

    conn = ensure_db()
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
