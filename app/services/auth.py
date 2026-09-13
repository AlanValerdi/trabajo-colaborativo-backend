from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.core.config import settings
from datetime import timedelta


def register_user(db: Session, data: RegisterRequest) -> User:
    """Crea un nuevo usuario. Lanza 400 si el email ya existe."""
    existing = db.scalars(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya esta registrado",
        )
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Busca el usuario por email y verifica la contrasena. Lanza 401 si falla."""
    user = db.scalars(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario desactivado",
        )
    return user


def login(db: Session, data: LoginRequest) -> TokenResponse:
    """Autentica al usuario y retorna access_token + refresh_token."""
    user = authenticate_user(db, data.email, data.password)

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})

    # Guardar refresh token hasheado en DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


def refresh_access_token(db: Session, data: RefreshRequest) -> AccessTokenResponse:
    """Genera un nuevo access token a partir de un refresh token valido."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido para esta operacion",
        )

    db_token = db.scalars(
        select(RefreshToken).where(
            RefreshToken.token == data.refresh_token,
            RefreshToken.revoked == False,  # noqa: E712
        )
    ).first()

    if not db_token or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
        )

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o desactivado",
        )

    new_access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return AccessTokenResponse(access_token=new_access_token)


def logout(db: Session, refresh_token: str) -> None:
    """Revoca el refresh token para cerrar sesion."""
    db_token = db.scalars(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    ).first()
    if db_token:
        db_token.revoked = True
        db.commit()
