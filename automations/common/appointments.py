"""
Parseo de fecha/hora en lenguaje natural + calendario de disponibilidad,
compartido entre la demo simulada (`citas-booking`) y el bot de Telegram
(`telegram-bot`).

100% basado en reglas — no depende de ninguna IA, para que agendar sea
determinístico y confiable siempre.
"""
import re
import sqlite3
from datetime import date, timedelta, time, datetime

WEEKDAYS = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

BUSINESS_HOURS = range(9, 17)  # 9am a 4pm (última cita 16:00)
DAYS_AHEAD_TO_SEED = 14


def parse_preferred_date(text: str, today: date):
    lowered = text.lower()
    if "pasado mañana" in lowered or "pasado manana" in lowered:
        return today + timedelta(days=2)
    if "mañana" in lowered or "manana" in lowered:
        return today + timedelta(days=1)
    if "hoy" in lowered:
        return today
    for name, idx in WEEKDAYS.items():
        if name in lowered:
            days_ahead = (idx - today.weekday()) % 7
            days_ahead = days_ahead or 7
            return today + timedelta(days=days_ahead)
    return None


def parse_preferred_time(text: str):
    lowered = text.lower()

    m = re.search(r"\b(\d{1,2}):(\d{2})\b", lowered)
    if m:
        return time(hour=int(m.group(1)) % 24, minute=int(m.group(2)))

    m = re.search(r"(?:a las\s+)?(\d{1,2})\s*(am|pm)\b", lowered)
    if m:
        hour = int(m.group(1))
        period = m.group(2)
        if period == "pm" and hour < 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0
        return time(hour=hour % 24, minute=0)

    m = re.search(r"a las\s+(\d{1,2})\s*(de la mañana|de la manana|de la tarde|de la noche)?", lowered)
    if m:
        hour = int(m.group(1))
        period = m.group(2) or ""
        if "tarde" in period or "noche" in period:
            if hour < 12:
                hour += 12
        elif "mañana" in period or "manana" in period:
            if hour == 12:
                hour = 0
        else:
            if hour < 9:
                hour += 12
        return time(hour=hour % 24, minute=0)

    return None


def format_date_es(d: date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def ensure_appointments_db(db_path):
    conn = sqlite3.connect(db_path)
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
