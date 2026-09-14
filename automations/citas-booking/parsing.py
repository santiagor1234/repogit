"""Parseo de fecha/hora preferida a partir de lenguaje natural en español.

100% basado en reglas (regex + diccionarios) — no depende de ninguna IA,
para que agendar una cita sea determinístico y confiable siempre.
"""
import re
from datetime import date, timedelta, time

WEEKDAYS = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


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
