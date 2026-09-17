from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.campus import Campus
from app.models.faculty import Faculty
from app.models.location import Location
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


def list_campuses(db: Session) -> list[CampusRead]:
    campuses = list(db.scalars(select(Campus).order_by(Campus.code)).all())
    return [CampusRead.model_validate(campus) for campus in campuses]


def create_campus(db: Session, campus_in: CampusCreate) -> CampusRead:
    existing = db.scalar(select(Campus).where(Campus.code == campus_in.code))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un campus con ese código",
        )
    campus = Campus(code=campus_in.code, name=campus_in.name)
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return CampusRead.model_validate(campus)


def update_campus(db: Session, campus_id: int, campus_in: CampusUpdate) -> CampusRead:
    campus = db.get(Campus, campus_id)
    if campus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campus no encontrado",
        )
    if campus_in.code is not None and campus_in.code != campus.code:
        existing = db.scalar(select(Campus).where(Campus.code == campus_in.code))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un campus con ese código",
            )
        campus.code = campus_in.code
    if campus_in.name is not None:
        campus.name = campus_in.name
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return CampusRead.model_validate(campus)


def delete_campus(db: Session, campus_id: int) -> None:
    campus = db.get(Campus, campus_id)
    if campus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campus no encontrado",
        )
    faculties = db.scalars(select(Faculty).where(Faculty.campus_id == campus_id)).first()
    if faculties is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un campus que tiene facultades asociadas",
        )
    db.delete(campus)
    db.commit()


def list_faculties(db: Session, campus_id: int | None = None) -> list[FacultyRead]:
    query = select(Faculty).order_by(Faculty.name)
    if campus_id is not None:
        query = query.where(Faculty.campus_id == campus_id)
    faculties = list(db.scalars(query).all())
    return [FacultyRead.model_validate(faculty) for faculty in faculties]


def create_faculty(db: Session, faculty_in: FacultyCreate) -> FacultyRead:
    campus = db.get(Campus, faculty_in.campus_id)
    if campus is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campus no encontrado",
        )
    faculty = Faculty(campus_id=faculty_in.campus_id, name=faculty_in.name)
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return FacultyRead.model_validate(faculty)


def update_faculty(db: Session, faculty_id: int, faculty_in: FacultyUpdate) -> FacultyRead:
    faculty = db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada",
        )
    if faculty_in.campus_id is not None:
        campus = db.get(Campus, faculty_in.campus_id)
        if campus is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campus no encontrado",
            )
        faculty.campus_id = faculty_in.campus_id
    if faculty_in.name is not None:
        faculty.name = faculty_in.name
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return FacultyRead.model_validate(faculty)


def delete_faculty(db: Session, faculty_id: int) -> None:
    faculty = db.get(Faculty, faculty_id)
    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada",
        )
    location = db.scalars(select(Location).where(Location.faculty_id == faculty_id)).first()
    if location is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una facultad que tiene ubicaciones asociadas",
        )
    db.delete(faculty)
    db.commit()


def list_locations(db: Session, faculty_id: int | None = None) -> list[LocationRead]:
    query = select(Location).order_by(Location.name)
    if faculty_id is not None:
        query = query.where(Location.faculty_id == faculty_id)
    locations = list(db.scalars(query).all())
    return [LocationRead.model_validate(location) for location in locations]


def create_location(db: Session, location_in: LocationCreate) -> LocationRead:
    faculty = db.get(Faculty, location_in.faculty_id)
    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facultad no encontrada",
        )
    location = Location(faculty_id=location_in.faculty_id, name=location_in.name)
    db.add(location)
    db.commit()
    db.refresh(location)
    return LocationRead.model_validate(location)


def update_location(db: Session, location_id: int, location_in: LocationUpdate) -> LocationRead:
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no encontrada",
        )
    if location_in.faculty_id is not None:
        faculty = db.get(Faculty, location_in.faculty_id)
        if faculty is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facultad no encontrada",
            )
        location.faculty_id = location_in.faculty_id
    if location_in.name is not None:
        location.name = location_in.name
    db.add(location)
    db.commit()
    db.refresh(location)
    return LocationRead.model_validate(location)


def delete_location(db: Session, location_id: int) -> None:
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no encontrada",
        )
    db.delete(location)
    db.commit()
