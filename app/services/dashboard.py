from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import func, select, case
from sqlmodel import Session
from app.db.database import engine
from app.models.report import Report
from app.models.specialty import Specialty

def obtener_resumen_dashboard() -> Dict[str, Any]:
    with Session(engine) as db:
        activos_estados = ['reportada', 'validada', 'asignada', 'en_progreso', 'en_proceso', 'bloqueada', 'reabierta']
        resueltos_estados = ['resuelta', 'cerrada']
        ahora = datetime.utcnow()

        # 1. Conteo de KPIs generales
        total_activas = db.scalar(
            select(func.count(Report.id)).where(func.lower(Report.status).in_(activos_estados))
        ) or 0

        en_progreso = db.scalar(
            select(func.count(Report.id)).where(func.lower(Report.status).in_(['en_progreso', 'en_proceso']))
        ) or 0

        bloqueadas = db.scalar(
            select(func.count(Report.id)).where(func.lower(Report.status) == 'bloqueada')
        ) or 0

        resueltas = db.scalar(
            select(func.count(Report.id)).where(func.lower(Report.status).in_(resueltos_estados))
        ) or 0

        vencidas = 0
        if hasattr(Report, 'due_date'):
            vencidas = db.scalar(
                select(func.count(Report.id)).where(
                    func.lower(Report.status).in_(activos_estados),
                    Report.due_date != None,
                    Report.due_date < ahora
                )
            ) or 0

        # 2. Desglose por Área usando scalars() para obtener las entidades completas
        areas_data: List[Dict[str, Any]] = []
        specialties = db.scalars(select(Specialty)).all()

        for esp in specialties:
            total_esp = db.scalar(
                select(func.count(Report.id)).where(
                    Report.specialty_id == esp.id,
                    func.lower(Report.status).in_(activos_estados)
                )
            ) or 0

            bloq_esp = db.scalar(
                select(func.count(Report.id)).where(
                    Report.specialty_id == esp.id,
                    func.lower(Report.status) == 'bloqueada'
                )
            ) or 0

            venc_esp = 0
            if hasattr(Report, 'due_date'):
                venc_esp = db.scalar(
                    select(func.count(Report.id)).where(
                        Report.specialty_id == esp.id,
                        func.lower(Report.status).in_(activos_estados),
                        Report.due_date != None,
                        Report.due_date < ahora
                    )
                ) or 0

            if total_esp > 0 or esp.id in [1, 2, 3]:
                areas_data.append({
                    "area_id": esp.id,
                    "area_nombre": esp.name,
                    "total_incidencias": total_esp,
                    "bloqueadas": bloq_esp,
                    "vencidas": venc_esp
                })

        return {
            "kpis": {
                "total_activas": total_activas,
                "en_progreso": en_progreso,
                "bloqueadas": bloqueadas,
                "vencidas": vencidas,
                "resueltas": resueltas
            },
            "areas": areas_data,
            "alertas_vencidas": []
        }
