from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
# Asegúrate de importar los modelos correctos de tu proyecto (ejemplo: Reporte, Area, Usuario)
from app.models import Reporte, Area

def obtener_metricas_dashboard(db: Session):
    ahora = datetime.utcnow()

    # 1. Conteo real de KPIs
    total_activas = db.query(Reporte).filter(Reporte.estado.notin_(['resuelto', 'cerrado', 'cancelado'])).count()
    en_progreso = db.query(Reporte).filter(Reporte.estado == 'en_progreso').count()
    bloqueadas = db.query(Reporte).filter(Reporte.estado == 'bloqueada').count()
    resueltas = db.query(Reporte).filter(Reporte.estado.in_(['resuelto', 'cerrado'])).count()

    # Vencidas: incidencias no concluidas cuya fecha_limite o sla ya venció
    vencidas = db.query(Reporte).filter(
        Reporte.estado.notin_(['resuelto', 'cerrado', 'cancelado']),
        Reporte.fecha_limite != None,
        Reporte.fecha_limite < ahora
    ).count()

    # 2. Resumen real agrupado por Área
    areas_query = db.query(
        Area.id.label('area_id'),
        Area.nombre.label('area_nombre'),
        func.count(Reporte.id).label('total_incidencias')
    ).outerjoin(Reporte, Reporte.area_id == Area.id)\
     .group_by(Area.id, Area.nombre).all()

    areas_list = []
    for a in areas_query:
        bloq = db.query(Reporte).filter(Reporte.area_id == a.area_id, Reporte.estado == 'bloqueada').count()
        venc = db.query(Reporte).filter(
            Reporte.area_id == a.area_id,
            Reporte.estado.notin_(['resuelto', 'cerrado', 'cancelado']),
            Reporte.fecha_limite != None,
            Reporte.fecha_limite < ahora
        ).count()
        areas_list.append({
            "area_id": a.area_id,
            "area_nombre": a.area_nombre,
            "total_incidencias": a.total_incidencias,
            "bloqueadas": bloq,
            "vencidas": venc
        })

    # 3. Lista de incidencias vencidas reales (HU-22)
    vencidas_records = db.query(Reporte).filter(
        Reporte.estado.notin_(['resuelto', 'cerrado', 'cancelado']),
        Reporte.fecha_limite != None,
        Reporte.fecha_limite < ahora
    ).limit(10).all()

    alertas = []
    for inc in vencidas_records:
        horas_vencida = int((ahora - inc.fecha_limite).total_seconds() // 3600) if inc.fecha_limite else 0
        alertas.append({
            "id": inc.id,
            "folio": getattr(inc, 'folio', f"INC-{inc.id:04d}"),
            "titulo": getattr(inc, 'titulo', 'Sin título'),
            "estado": getattr(inc, 'estado', 'en_progreso'),
            "prioridad": getattr(inc, 'prioridad', 'media'),
            "area_nombre": inc.area.nombre if getattr(inc, 'area', None) else 'General',
            "tecnico_nombre": inc.tecnico.nombre if getattr(inc, 'tecnico', None) else 'Sin asignar',
            "horas_vencida": max(1, horas_vencida)
        })

    return {
        "kpis": {
            "total_activas": total_activas,
            "en_progreso": en_progreso,
            "bloqueadas": bloqueadas,
            "vencidas": vencidas,
            "resueltas": resueltas
        },
        "areas": areas_list,
        "alertas_vencidas": alertas
    }
