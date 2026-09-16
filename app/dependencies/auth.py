from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from sqlmodel import select

from app.core.security import decode_token
from app.db.database import get_db
from app.models.role import RoleEnum
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    CAPA 2 de seguridad: decodifica el JWT y retorna el usuario autenticado.
    Lanza 401 si el token es invalido, expirado, o el usuario no existe/esta desactivado.
    """
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido para esta operacion",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(User).options(selectinload(User.user_roles)).where(User.id == int(user_id))
    )
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o desactivado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*roles: RoleEnum):
    """
    CAPA 3 de seguridad: factory que genera un Depends que valida el rol del usuario.
    Uso: dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))]
    Lanza 403 si ninguno de los roles del usuario esta permitido.
    """
    def guard(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_any_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Roles permitidos: {[r.value for r in roles]}",
            )
        return current_user
    return guard
