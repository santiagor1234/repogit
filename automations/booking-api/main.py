"""
API de reservas — el backend real detrás de la web de agendamiento
(`docs/demos.md` / artifact de reservas). Recibe y guarda citas de
verdad en una base de datos, para que "Agendar cita" en la web y en el
bot de Telegram apunten al mismo sistema.

Endpoints:
    GET  /health                          — chequeo de salud
    GET  /availability?business=X&date=Y  — horarios libres/ocupados de un día
    POST /bookings                        — crea una reserva (rechaza si el horario ya está tomado)
    GET  /bookings?business=X             — lista las reservas de un negocio (sin auth todavía — ver README)

Uso local:
    uvicorn main:app --reload

En producción (Render, etc.) el comando de arranque es:
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""
import hashlib
import os
import sqlite3
from datetime import date as date_cls, datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = os.getenv("DB_PATH", "citas.db")
SLOT_MINUTES = 30
BUSINESS_HOURS = (9, 17)  # abre 9:00, última cita empieza antes de las 17:00

app = FastAPI(title="Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # la web de reservas se sirve desde el dominio de Claude Artifacts
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            service TEXT,
            date TEXT,
            time TEXT,
            client_name TEXT,
            phone TEXT,
            note TEXT,
            code TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_slot ON appointments (business, date, time)")
    conn.commit()
    return conn


def slots_for_date(d: date_cls):
    slots = []
    t = datetime.combine(d, datetime.min.time()).replace(hour=BUSINESS_HOURS[0])
    end = datetime.combine(d, datetime.min.time()).replace(hour=BUSINESS_HOURS[1])
    while t < end:
        slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=SLOT_MINUTES)
    return slots


class BookingIn(BaseModel):
    business: str
    service: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    client_name: str
    phone: str
    note: str = ""


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/availability")
def availability(business: str = Query(...), date: str = Query(...)):
    try:
        d = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida, formato esperado YYYY-MM-DD")

    if d.weekday() >= 5:
        return {"date": date, "slots": []}

    conn = get_db()
    taken = {
        row[0]
        for row in conn.execute(
            "SELECT time FROM appointments WHERE business = ? AND date = ?", (business, date)
        )
    }
    slots = [{"time": t, "available": t not in taken} for t in slots_for_date(d)]
    return {"date": date, "slots": slots}


@app.post("/bookings")
def create_booking(b: BookingIn):
    try:
        d = date_cls.fromisoformat(b.date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida, formato esperado YYYY-MM-DD")
    if d.weekday() >= 5:
        raise HTTPException(400, "Cerrado ese día")
    if b.time not in slots_for_date(d):
        raise HTTPException(400, "Ese horario no existe en la agenda")

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM appointments WHERE business = ? AND date = ? AND time = ?",
        (b.business, b.date, b.time),
    ).fetchone()
    if existing:
        raise HTTPException(409, "Ese horario ya fue reservado, elegí otro")

    code = hashlib.sha1(f"{b.business}{b.date}{b.time}{b.client_name}{datetime.now()}".encode()).hexdigest()[:6].upper()
    conn.execute(
        "INSERT INTO appointments (business, service, date, time, client_name, phone, note, code, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (b.business, b.service, b.date, b.time, b.client_name, b.phone, b.note, code, datetime.now().isoformat()),
    )
    conn.commit()
    return {"ok": True, "code": code}


@app.get("/bookings")
def list_bookings(business: str = Query(...)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, service, date, time, client_name, phone, note, code, created_at "
        "FROM appointments WHERE business = ? ORDER BY date, time",
        (business,),
    ).fetchall()
    cols = ["id", "service", "date", "time", "client_name", "phone", "note", "code", "created_at"]
    return [dict(zip(cols, row)) for row in rows]
