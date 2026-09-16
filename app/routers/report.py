from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.schemas.upload import ImageUploadResponse
from app.services import report as report_service
from app.services import upload as upload_service

router = APIRouter()


@router.post(
    "/images",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir imagen para un reporte",
)
async def upload_report_image(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    image_url = await upload_service.save_report_image(
        file,
        Path(settings.UPLOAD_DIR),
        settings.PUBLIC_BASE_URL,
    )
    return ImageUploadResponse(image_url=image_url)


@router.post(
    "/",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reporte (version minima, para poder probar HU-4)",
)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Alta minima de incidencias. El formulario completo (HU-05/06) lo entrega
    Equipo 1; este endpoint existe para no bloquear las pruebas de consulta
    y seguimiento (HU-4) mientras tanto.
    """
    return report_service.create_report(db, current_user.id, report_in)


@router.get(
    "/",
    response_model=list[ReportRead],
    summary="Listar incidencias reportadas (HU-4)",
)
def list_reports(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return report_service.list_reports(db)


@router.get(
    "/{folio}",
    response_model=ReportRead,
    summary="Consultar incidencia por folio (HU-4)",
)
def get_report(
    folio: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    report = report_service.get_report(db, folio)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )
    return report


@router.patch(
    "/{folio}",
    response_model=ReportRead,
    summary="Actualizar reporte en estado Creado",
)
def update_report(
    folio: str,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.update_report(db, folio, current_user.id, report_in)


@router.delete(
    "/{folio}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar reporte en estado Creado",
)
def delete_report(
    folio: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report_service.delete_report(db, folio, current_user.id)
