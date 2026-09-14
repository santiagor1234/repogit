"""
Demo: AI Lead Finder + Outreach personalizado

Dado un nicho y una ciudad, genera una lista de prospectos (negocios) y
un mensaje de contacto personalizado por IA para cada uno, listo para
enviar por email/WhatsApp/Instagram.

Uso:
    python main.py --niche "dentistas" --city "Bogotá" --count 8

IMPORTANTE: los leads generados aquí son SINTÉTICOS (con Faker), para que
la demo corra sin depender de una API externa. En producción, el paso de
"generar leads" se reemplaza por una fuente real: Google Maps Places API,
scraping de directorios públicos, o listas propias del cliente — el resto
del pipeline (personalización + guardado) es igual.
"""
import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from faker import Faker

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common.ai import complete, is_live, provider_label  # noqa: E402
from niches import pain_point_for  # noqa: E402

DB_PATH = Path(__file__).parent / "leads.db"
OUTPUT_DIR = Path(__file__).parent / "output"

fake = Faker("es_MX")


def generate_leads(niche: str, city: str, count: int):
    leads = []
    for _ in range(count):
        company = f"{fake.last_name()} {niche.title()}"
        leads.append(
            {
                "company": company,
                "city": city,
                "contact_name": fake.first_name(),
                "phone": fake.phone_number(),
                "email": f"contacto@{company.lower().replace(' ', '')}.com",
            }
        )
    return leads


def draft_outreach(company: str, contact_name: str, niche: str, city: str) -> str:
    pain_point = pain_point_for(niche)
    fallback = (
        f"Hola {contact_name}, vi que {company} es referente en {niche} en {city}. "
        f"Ayudo a negocios como el suyo a resolver {pain_point} con automatización, "
        f"sin agregar trabajo al equipo. ¿Tenés 10 min esta semana para mostrarte cómo?"
    )
    return complete(
        prompt=(
            f'Escribe un mensaje corto (máx 3 líneas) de primer contacto en frío para "{company}", '
            f"un negocio de {niche} en {city}, ofreciendo automatizar: {pain_point}. "
            f"Dirígete a {contact_name}. Tono cercano, profesional, sin sonar a spam, en español."
        ),
        fallback=fallback,
        system="Eres un experto en outreach B2B que escribe mensajes de primer contacto breves y efectivos.",
    )


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            niche TEXT,
            city TEXT,
            contact_name TEXT,
            phone TEXT,
            email TEXT,
            outreach_message TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="dentistas")
    parser.add_argument("--city", default="Bogotá")
    parser.add_argument("--count", type=int, default=8)
    args = parser.parse_args()

    mode = f"IA real ({provider_label()})" if is_live() else "modo demo (sin API key, mensajes por plantilla)"
    print(f"AI Lead Finder + Outreach — {mode}")
    print(f"Nicho: {args.niche} | Ciudad: {args.city} | Leads: {args.count}")
    print("=" * 60)

    leads = generate_leads(args.niche, args.city, args.count)
    conn = ensure_db()
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / f"leads_{args.niche.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["company", "city", "contact_name", "phone", "email", "outreach_message"])

        for lead in leads:
            message = draft_outreach(lead["company"], lead["contact_name"], args.niche, args.city)
            print(f"\n{lead['company']} — {lead['contact_name']} ({lead['email']})")
            print(f"  {message}")

            writer.writerow([lead["company"], lead["city"], lead["contact_name"], lead["phone"], lead["email"], message])
            conn.execute(
                "INSERT INTO prospects (company, niche, city, contact_name, phone, email, outreach_message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (lead["company"], args.niche, lead["city"], lead["contact_name"], lead["phone"], lead["email"], message, datetime.now().isoformat()),
            )

    conn.commit()
    conn.close()
    print(f"\n{'=' * 60}")
    print(f"{len(leads)} leads generados -> {csv_path.relative_to(Path(__file__).parent)} y leads.db (tabla `prospects`)")


if __name__ == "__main__":
    main()
