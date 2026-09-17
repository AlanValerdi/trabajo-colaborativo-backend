from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.role import RoleEnum
from app.models.user import User
from app.schemas.catalog import (
    CampusCreate,
    CampusRead,
    CampusUpdate,
    FacultyCreate,
    FacultyRead,
    FacultyUpdate,
    LocationCreate,
    LocationRead,
    LocationUpdate,
)
from app.services import catalog as catalog_service

campus_router = APIRouter()
faculty_router = APIRouter()
location_router = APIRouter()


@campus_router.get("/", response_model=list[CampusRead], summary="Listar campuses")
def list_campuses(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return catalog_service.list_campuses(db)


@campus_router.post(
    "/",
    response_model=CampusRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear campus",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def create_campus(campus_in: CampusCreate, db: Session = Depends(get_db)):
    return catalog_service.create_campus(db, campus_in)


@campus_router.patch(
    "/{campus_id}",
    response_model=CampusRead,
    summary="Actualizar campus",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def update_campus(campus_id: int, campus_in: CampusUpdate, db: Session = Depends(get_db)):
    return catalog_service.update_campus(db, campus_id, campus_in)


@campus_router.delete(
    "/{campus_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar campus",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def delete_campus(campus_id: int, db: Session = Depends(get_db)):
    catalog_service.delete_campus(db, campus_id)


@faculty_router.get("/", response_model=list[FacultyRead], summary="Listar facultades")
def list_faculties(
    campus_id: int | None = Query(default=None, alias="campusId"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return catalog_service.list_faculties(db, campus_id)


@faculty_router.post(
    "/",
    response_model=FacultyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear facultad",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def create_faculty(faculty_in: FacultyCreate, db: Session = Depends(get_db)):
    return catalog_service.create_faculty(db, faculty_in)


@faculty_router.patch(
    "/{faculty_id}",
    response_model=FacultyRead,
    summary="Actualizar facultad",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def update_faculty(faculty_id: int, faculty_in: FacultyUpdate, db: Session = Depends(get_db)):
    return catalog_service.update_faculty(db, faculty_id, faculty_in)


@faculty_router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar facultad",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    catalog_service.delete_faculty(db, faculty_id)


@location_router.get("/", response_model=list[LocationRead], summary="Listar ubicaciones")
def list_locations(
    faculty_id: int | None = Query(default=None, alias="facultyId"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return catalog_service.list_locations(db, faculty_id)


@location_router.post(
    "/",
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ubicación",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def create_location(location_in: LocationCreate, db: Session = Depends(get_db)):
    return catalog_service.create_location(db, location_in)


@location_router.patch(
    "/{location_id}",
    response_model=LocationRead,
    summary="Actualizar ubicación",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def update_location(location_id: int, location_in: LocationUpdate, db: Session = Depends(get_db)):
    return catalog_service.update_location(db, location_id, location_in)


@location_router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar ubicación",
    dependencies=[Depends(require_roles(RoleEnum.ADMINISTRADOR))],
)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    catalog_service.delete_location(db, location_id)
