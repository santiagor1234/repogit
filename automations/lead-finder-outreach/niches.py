"""Pain points típicos por nicho, usados para personalizar el outreach de la demo."""

NICHE_PAIN_POINTS = {
    "dentistas": "pacientes que no confirman ni cancelan turnos a tiempo",
    "restaurantes": "reservas perdidas por no responder rápido en redes sociales",
    "gimnasios": "bajo seguimiento a leads que preguntan por membresías y nunca vuelven a escribir",
    "inmobiliarias": "responder tarde a interesados en una propiedad, perdiendo la venta frente a otra inmobiliaria",
    "abogados": "consultas iniciales que se pierden por no dar seguimiento rápido",
    "veterinarias": "recordatorios de vacunas/controles que se hacen manualmente y se olvidan",
    "spa y estética": "agenda desorganizada y muchos no-shows sin recordatorio automático",
    "agencias de marketing": "reportes de resultados para clientes que toman horas armar a mano",
}

DEFAULT_PAIN_POINT = "procesos manuales que le quitan tiempo al equipo y ralentizan la respuesta a clientes"


def pain_point_for(niche: str) -> str:
    return NICHE_PAIN_POINTS.get(niche.lower().strip(), DEFAULT_PAIN_POINT)
