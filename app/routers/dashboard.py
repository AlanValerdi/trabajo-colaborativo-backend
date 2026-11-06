from typing import Dict, Any

def obtener_resumen_dashboard() -> Dict[str, Any]:
    return {
        "kpis": {
            "total_activas": 18,
            "en_progreso": 7,
            "bloqueadas": 2,
            "vencidas": 3,
            "resueltas": 24
        },
        "areas": [
            {"area_id": 1, "area_nombre": "Mantenimiento TI", "total_incidencias": 8, "bloqueadas": 2, "vencidas": 1},
            {"area_id": 2, "area_nombre": "Infraestructura y Obras", "total_incidencias": 6, "bloqueadas": 0, "vencidas": 2},
            {"area_id": 3, "area_nombre": "Adquisiciones y Almacén", "total_incidencias": 4, "bloqueadas": 0, "vencidas": 0}
        ],
        "alertas_vencidas": [
            {
                "id": 42,
                "folio": "INC-2026-0042",
                "titulo": "Proyector sin imagen en aula 204",
                "estado": "bloqueada",
                "prioridad": "alta",
                "area_nombre": "Mantenimiento TI",
                "tecnico_nombre": "Carlos Núñez",
                "fecha_limite": "2026-10-31T14:00:00",
                "horas_vencida": 31
            },
            {
                "id": 35,
                "folio": "INC-2026-0035",
                "titulo": "Fuga de agua en sanitarios edificio FCC-2",
                "estado": "en_progreso",
                "prioridad": "alta",
                "area_nombre": "Infraestructura y Obras",
                "tecnico_nombre": "Ana Torres",
                "fecha_limite": "2026-11-01T10:00:00",
                "horas_vencida": 18
            },
            {
                "id": 48,
                "folio": "INC-2026-0048",
                "titulo": "Falla en centro de carga laboratorio 3",
                "estado": "en_progreso",
                "prioridad": "alta",
                "area_nombre": "Infraestructura y Obras",
                "tecnico_nombre": "Sin asignar",
                "fecha_limite": "2026-11-02T16:00:00",
                "horas_vencida": 8
            }
        ]
    }