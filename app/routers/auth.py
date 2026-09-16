from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.user import serialize_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Crea una nueva cuenta. El rol por defecto es **reportante**."""
    return auth_service.register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica al usuario con email y contrasena.
    Retorna un **access_token** (30 min) y un **refresh_token** (7 dias).
    """
    return auth_service.login(db, data)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Renovar access token",
)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Usa el refresh token para obtener un nuevo access token sin volver a logearse."""
    return auth_service.refresh_access_token(db, data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesion",
)
def logout(
    data: RefreshRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Revoca el refresh token. Requiere estar autenticado."""
    auth_service.logout(db, data.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Perfil del usuario autenticado",
)
def me(current_user: User = Depends(get_current_user)):
    """Retorna el perfil del usuario dueno del token."""
    return serialize_user(current_user)
