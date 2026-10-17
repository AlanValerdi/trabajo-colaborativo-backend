from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.comment import Comment, CommentMention
from app.models.report import Report
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.comment import CommentAuthor, CommentMentionRead, CommentRead


def _serialize(
    comment: Comment,
    author: User | None,
    mentioned: list[User],
) -> CommentRead:
    return CommentRead(
        id=comment.id,
        report_id=comment.report_id,
        user_id=comment.user_id,
        author=CommentAuthor(
            id=comment.user_id,
            name=author.name if author else "Usuario",
        ),
        content=comment.content,
        mentions=[CommentMentionRead(id=user.id, name=user.name) for user in mentioned],
        created_at=comment.created_at,
    )


def _mentions_for(db: Session, comment_ids: list[int]) -> dict[int, list[User]]:
    if not comment_ids:
        return {}
    rows = db.scalars(
        select(CommentMention).where(CommentMention.comment_id.in_(comment_ids))
    ).all()
    if not rows:
        return {}
    user_ids = {row.user_id for row in rows}
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all()
    user_map = {user.id: user for user in users}
    result: dict[int, list[User]] = {}
    for row in rows:
        user = user_map.get(row.user_id)
        if user is not None:
            result.setdefault(row.comment_id, []).append(user)
    return result


def _validate_mentions(db: Session, mention_ids: list[int]) -> list[User]:
    unique_ids = list(dict.fromkeys(mention_ids))
    users = list(db.scalars(select(User).where(User.id.in_(unique_ids))).all())
    found = {user.id for user in users}
    missing = [str(uid) for uid in unique_ids if uid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No existen los usuarios mencionados: {', '.join(missing)}",
        )
    return users


def get_comments_by_report(db: Session, report_id: int) -> list[CommentRead]:
    comments = list(
        db.scalars(
            select(Comment)
            .where(Comment.report_id == report_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
        ).all()
    )
    if not comments:
        return []

    author_ids = {comment.user_id for comment in comments}
    authors = db.scalars(select(User).where(User.id.in_(author_ids))).all()
    author_map = {user.id: user for user in authors}
    mentions_map = _mentions_for(db, [comment.id for comment in comments])
    return [
        _serialize(
            comment,
            author_map.get(comment.user_id),
            mentions_map.get(comment.id, []),
        )
        for comment in comments
    ]


def create_comment(
    db: Session,
    report_id: int,
    user: User,
    content: str,
    mention_ids: list[int] | None = None,
) -> CommentRead:
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido del comentario no puede estar vacío.",
        )

    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un reporte con ese id.",
        )

    mentioned = _validate_mentions(db, mention_ids) if mention_ids else []

    comment = Comment(report_id=report_id, user_id=user.id, content=content.strip())
    db.add(comment)
    db.flush()

    for mentioned_user in mentioned:
        db.add(CommentMention(comment_id=comment.id, user_id=mentioned_user.id))

    db.commit()
    db.refresh(comment)
    return _serialize(comment, user, mentioned)


def update_comment(
    db: Session,
    comment_id: int,
    current_user: User,
    new_content: str,
) -> CommentRead:
    comment = db.get(Comment, comment_id)
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
    author = db.get(User, comment.user_id)
    mentions_map = _mentions_for(db, [comment.id])
    return _serialize(comment, author, mentions_map.get(comment.id, []))


def delete_comment(db: Session, comment_id: int, current_user: User) -> None:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado.",
        )

    # REGLA: Puede eliminar el autor o un administrador
    is_author = comment.user_id == current_user.id
    is_admin = current_user.has_any_role(RoleEnum.ADMINISTRADOR)

    if not (is_author or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este comentario.",
        )

    for mention in db.scalars(
        select(CommentMention).where(CommentMention.comment_id == comment.id)
    ).all():
        db.delete(mention)
    db.delete(comment)
    db.commit()
