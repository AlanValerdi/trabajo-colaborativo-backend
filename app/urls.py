from fastapi import FastAPI

from app.routers import auth as auth_router
from app.routers import user as user_router
from app.routers import report as report_router


def register_routers(app: FastAPI) -> None:
    """
    Archivo central de rutas.
    Todos los routers del sistema se registran aqui.
    Para agregar un nuevo modulo: importarlo y anadir su include_router.
    """

    app.include_router(
        auth_router.router,
        prefix="/auth",
        tags=["Auth"],
    )

    app.include_router(
        user_router.router,
        prefix="/users",
        tags=["Users"],
    )

    app.include_router(
        report_router.router,
        prefix="/reports",
        tags=["Reports"],
    )
