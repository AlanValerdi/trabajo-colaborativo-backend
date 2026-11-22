import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.report import Report, ReportPriorityEnum, ReportStatusEnum
from app.models.report_status_event import ReportStatusEvent
from app.models.role import RoleEnum
from app.models.specialty import IncidentCategoryEnum
from app.models.user import User
from app.models.user_role import UserRole


class ReportSummaryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.manager = User(
            name="Manager",
            email="manager@example.com",
            password_hash="unused",
        )
        self.manager.user_roles = [UserRole(role=RoleEnum.COORDINADOR)]
        self.technician = User(
            name="Technician",
            email="technician@example.com",
            password_hash="unused",
        )
        self.technician.user_roles = [UserRole(role=RoleEnum.TECNICO)]
        self.db.add_all([self.manager, self.technician])
        self.db.commit()

        now = datetime.now(timezone.utc)
        self.closed_report = Report(
            folio="closed-report",
            title="Resolved issue",
            description="Description",
            campus_label="Campus",
            faculty_label="Faculty",
            space_label="Building A",
            location_id=5,
            specialty_id=2,
            category=IncidentCategoryEnum.ELECTRICIDAD,
            priority=ReportPriorityEnum.ALTA,
            status=ReportStatusEnum.CERRADA,
            assignee_id=self.technician.id,
            author_id=self.manager.id,
            created_at=now - timedelta(hours=10),
            updated_at=now,
        )
        self.open_report = Report(
            folio="open-report",
            title="Open issue",
            description="Description",
            campus_label="Campus",
            faculty_label="Faculty",
            space_label="Building B",
            location_id=6,
            specialty_id=2,
            category=IncidentCategoryEnum.AGUA,
            priority=ReportPriorityEnum.CRITICA,
            status=ReportStatusEnum.EN_PROGRESO,
            author_id=self.manager.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add_all([self.closed_report, self.open_report])
        self.db.commit()
        self.db.add(
            ReportStatusEvent(
                report_id=self.closed_report.id,
                from_status=ReportStatusEnum.RESUELTA,
                to_status=ReportStatusEnum.CERRADA,
                actor_id=self.manager.id,
                created_at=now,
            )
        )
        self.db.commit()

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: self.manager
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def test_summary_metrics_filters_and_pagination(self):
        response = self.client.get(
            "/reports/summary",
            params={
                "start_date": self.closed_report.created_at.date().isoformat(),
                "end_date": self.closed_report.created_at.date().isoformat(),
                "category_id": "electricidad",
                "area_id": 2,
                "location_id": 5,
                "status": "cerrada",
                "priority": "alta",
                "limit": 1,
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["kpis"]["total"], 1)
        self.assertEqual(data["kpis"]["resolved_closed"], 1)
        self.assertAlmostEqual(data["kpis"]["average_resolution_hours"], 10, places=2)
        self.assertEqual(data["items"][0]["title"], "Resolved issue")
        self.assertEqual(data["items"][0]["assignee"], "Technician")
        self.assertEqual(data["items"][0]["location"], "Building A")
        self.assertIsNotNone(data["items"][0]["closed_at"])
        self.assertEqual(data["by_category"], [{"category": "electricidad", "count": 1}])
        self.assertEqual(data["by_building"][0]["location_id"], 5)

    def test_aggregates_cover_all_matches_not_only_the_current_page(self):
        response = self.client.get("/reports/summary", params={"limit": 1})

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["kpis"]["total"], 2)
        self.assertEqual(data["kpis"]["open"], 1)
        self.assertEqual(data["kpis"]["in_progress"], 1)
        self.assertEqual(data["kpis"]["resolved_closed"], 1)
        self.assertAlmostEqual(data["kpis"]["average_resolution_hours"], 10, places=2)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(sum(row["count"] for row in data["by_category"]), 2)

    def test_critical_priority_filter(self):
        response = self.client.get(
            "/reports/summary",
            params={"priority": "critica"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(response.json()["items"][0]["priority"], "critica")

    def test_management_roles_only_and_query_validation(self):
        for role in [
            RoleEnum.COORDINADOR,
            RoleEnum.RESPONSABLE_AREA,
            RoleEnum.ADMINISTRADOR,
        ]:
            actor = User(
                id=100,
                name="Manager",
                email=f"{role.value}@example.com",
                password_hash="unused",
            )
            actor.user_roles = [UserRole(user_id=actor.id, role=role)]
            app.dependency_overrides[get_current_user] = lambda actor=actor: actor
            self.assertEqual(self.client.get("/reports/summary").status_code, 200)

        app.dependency_overrides[get_current_user] = lambda: self.technician
        self.assertEqual(self.client.get("/reports/summary").status_code, 403)

        app.dependency_overrides.pop(get_current_user)
        self.assertEqual(self.client.get("/reports/summary").status_code, 401)
        app.dependency_overrides[get_current_user] = lambda: self.manager
        self.assertEqual(
            self.client.get(
                "/reports/summary",
                params={"start_date": "2026-12-31", "end_date": "2026-01-01"},
            ).status_code,
            422,
        )
