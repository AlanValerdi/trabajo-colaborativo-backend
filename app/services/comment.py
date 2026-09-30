from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.comment import Comment


def get_comments_by_report(db: Session, report_id: int):
    return (
        db.query(Comment)
        .filter(Comment.report_id == report_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


def create_comment(db: Session, report_id: int, user_id: int, content: str) -> Comment:
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido del comentario no puede estar vacío.",
        )

    comment = Comment(report_id=report_id, user_id=user_id, content=content.strip())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment_id: int, current_user: any, new_content: str) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado.",
        )

    # REGLA: Únicamente el creador del comentario puede editar el texto
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor original puede editar este comentario.",
        )

    if not new_content or not new_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido no puede estar vacío.",
        )

    comment.content = new_content.strip()
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int, current_user: any) -> None:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado.",
        )

    # REGLA: Puede eliminar el autor o un administrador
    is_author = comment.user_id == current_user.id
    is_admin = getattr(current_user, "role", "") == "admin" or getattr(current_user, "is_admin", False)

    if not (is_author or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este comentario.",
        )

    db.delete(comment)
    db.commit()