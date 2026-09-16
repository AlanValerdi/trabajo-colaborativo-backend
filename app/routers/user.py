from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user as user_service

router = APIRouter()


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (solo administrador)",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user_in)


@router.get(
    "/",
    response_model=list[UserRead],
    summary="Listar usuarios",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR, RoleEnum.COORDINADOR))],
)
def list_users(db: Session = Depends(get_db)):
    return user_service.list_users(db)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Ver usuario por ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_roles = {RoleEnum.ADMINISTRADOR, RoleEnum.COORDINADOR}
    if current_user.id != user_id and not current_user.has_any_role(*allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario",
        )
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user_service.serialize_user(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="Asignar roles a un usuario",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def change_role(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    if user_in.roles is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos un rol en el campo roles",
        )
    user = user_service.update_user(db, user_id, user_in)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserRead,
    summary="Desactivar usuario",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.update_user(db, user_id, UserUpdate(is_active=False))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


@router.patch(
    "/{user_id}/activate",
    response_model=UserRead,
    summary="Activar usuario",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def activate_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.update_user(db, user_id, UserUpdate(is_active=True))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user
