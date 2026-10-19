"""
Pruebas del backend con SQLite (sin necesidad de MySQL ni Docker).

Cada prueba recibe una base de datos limpia con roles, usuarios, una
especialidad por categoría y una incidencia categorizada y asignada.
"""
import os
import tempfile

_DB_FILE = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SQLALCHEMY_DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp())

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

import app.models  # noqa: E402,F401  (registra las tablas)
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.report import Report, ReportPriorityEnum, ReportStatusEnum  # noqa: E402
from app.models.role import RoleEnum  # noqa: E402
from app.models.specialty import IncidentCategoryEnum, Specialty  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_role import UserRole  # noqa: E402


@pytest.fixture()
def db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_user(db, name: str, role: RoleEnum) -> User:
    user = User(name=name, email=f"{name.lower().replace(' ', '.')}@test.mx", password_hash=hash_password("x"))
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(UserRole(user_id=user.id, role=role))
    db.commit()
    return user


@pytest.fixture()
def world(db):
    """Usuarios por rol, especialidades y una incidencia en estado Asignada."""
    users = {
        "reportante": _make_user(db, "Marta Ruiz", RoleEnum.REPORTANTE),
        "tecnico": _make_user(db, "Carlos Nunez", RoleEnum.TECNICO),
        "tecnico2": _make_user(db, "Otro Tecnico", RoleEnum.TECNICO),
        "responsable": _make_user(db, "Ana Torres", RoleEnum.RESPONSABLE_AREA),
    }
    specialties = {}
    for code, name, cat in [
        ("TI", "Tecnologías de la información", IncidentCategoryEnum.TI),
        ("ELE", "Electricidad", IncidentCategoryEnum.ELECTRICIDAD),
    ]:
        sp = Specialty(code=code, name=name, category=cat)
        db.add(sp)
        db.commit()
        db.refresh(sp)
        specialties[cat] = sp

    report = Report(
        folio="INC-TEST-0001",
        title="Proyector sin imagen",
        description="No proyecta",
        campus_label="CU",
        space_label="Aula 204",
        author_id=users["reportante"].id,
        status=ReportStatusEnum.ASIGNADA,
        category=IncidentCategoryEnum.TI,
        specialty_id=specialties[IncidentCategoryEnum.TI].id,
        assignee_id=users["tecnico"].id,
        classified=True,
        priority=ReportPriorityEnum.ALTA,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"users": users, "specialties": specialties, "report": report}


@pytest.fixture()
def api(world):
    client = TestClient(app)

    def as_user(user: User) -> dict:
        token = create_access_token({"sub": str(user.id), "type": "access"})
        return {"Authorization": f"Bearer {token}"}

    client.as_user = as_user
    return client
