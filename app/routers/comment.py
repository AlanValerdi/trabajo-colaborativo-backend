from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services import comment as comment_service

router = APIRouter(tags=["Comments"])


@router.get(
    "/reports/{report_id}/comments",
    response_model=list[CommentRead],
    summary="Listar comentarios de una incidencia (HU-13)",
)
def get_comments(
    report_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return comment_service.get_comments_by_report(db, report_id)


@router.post(
    "/reports/{report_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Comentar incidencia con menciones opcionales (HU-13, HU-14)",
)
def create_comment(
    report_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return comment_service.create_comment(
        db,
        report_id=report_id,
        user=current_user,
        content=payload.content,
        mention_ids=payload.mentions,
    )


@router.put(
    "/comments/{comment_id}",
    response_model=CommentRead,
    summary="Editar comentario propio",
)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return comment_service.update_comment(
        db, comment_id=comment_id, current_user=current_user, new_content=payload.content
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar comentario",
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment_service.delete_comment(db, comment_id=comment_id, current_user=current_user)
    return None
