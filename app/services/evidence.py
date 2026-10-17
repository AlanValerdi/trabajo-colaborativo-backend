from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.core.config import settings
from app.models.evidence import EvidenceStageEnum, ReportEvidence
from app.models.report import Report, ReportStatusEnum
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.evidence import EvidenceRead, EvidenceUploader
from app.services import upload as upload_service

_STAFF_ROLES = {
    RoleEnum.TECNICO,
    RoleEnum.RESPONSABLE_AREA,
    RoleEnum.COORDINADOR,
    RoleEnum.ADMINISTRADOR,
    RoleEnum.VALIDADOR,
}


def _get_report(db: Session, folio: str) -> Report:
    report = db.scalar(select(Report).where(Report.folio == folio))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese folio",
        )
    return report


def _assert_can_attach(report: Report, actor: User) -> None:
    is_participant = actor.id in {report.author_id, report.assignee_id}
    if not (is_participant or actor.has_any_role(*_STAFF_ROLES)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los participantes de la incidencia pueden adjuntar evidencia",
        )
    if report.status == ReportStatusEnum.CERRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede adjuntar evidencia a una incidencia cerrada",
        )


def _uploader_for(user: User | None, uploader_id: int) -> EvidenceUploader:
    if user is None:
        return EvidenceUploader(id=uploader_id, name="Usuario")
    return EvidenceUploader(id=user.id, name=user.name)


def _serialize(evidence: ReportEvidence, user: User | None) -> EvidenceRead:
    return EvidenceRead(
        id=evidence.id,
        report_id=evidence.report_id,
        uploader_id=evidence.uploader_id,
        uploader=_uploader_for(user, evidence.uploader_id),
        file_url=evidence.file_url,
        caption=evidence.caption,
        stage=evidence.stage,
        created_at=evidence.created_at,
    )


# HU-17 — Adjuntar evidencia
async def create_evidence(
    db: Session,
    folio: str,
    actor: User,
    file: UploadFile,
    caption: Optional[str],
    stage: Optional[EvidenceStageEnum],
) -> EvidenceRead:
    report = _get_report(db, folio)
    _assert_can_attach(report, actor)

    file_url = await upload_service.save_evidence_file(
        file,
        Path(settings.UPLOAD_DIR),
        settings.PUBLIC_BASE_URL,
    )

    caption = caption.strip() if caption else None
    evidence = ReportEvidence(
        report_id=report.id,
        uploader_id=actor.id,
        file_url=file_url,
        caption=caption or None,
        stage=stage,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return _serialize(evidence, actor)


def list_evidences(db: Session, folio: str) -> list[EvidenceRead]:
    report = _get_report(db, folio)
    rows = list(
        db.scalars(
            select(ReportEvidence)
            .where(ReportEvidence.report_id == report.id)
            .order_by(ReportEvidence.created_at.asc(), ReportEvidence.id.asc())
        ).all()
    )
    if not rows:
        return []

    uploader_ids = {row.uploader_id for row in rows}
    users = db.scalars(select(User).where(User.id.in_(uploader_ids))).all()
    user_map = {user.id: user for user in users}
    return [_serialize(row, user_map.get(row.uploader_id)) for row in rows]
