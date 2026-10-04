from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import comment as comment_service

router = APIRouter(tags=["Comments"])


@router.get("/reports/{report_id}/comments")
def get_comments(report_id: int, db: Session = Depends(get_db)):
    return comment_service.get_comments_by_report(db, report_id)


@router.post("/reports/{report_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(
    report_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = payload.get("content", "")
    return comment_service.create_comment(
        db, report_id=report_id, user_id=current_user.id, content=content
    )


@router.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = payload.get("content", "")
    return comment_service.update_comment(
        db, comment_id=comment_id, current_user=current_user, new_content=content
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment_service.delete_comment(db, comment_id=comment_id, current_user=current_user)
    return None