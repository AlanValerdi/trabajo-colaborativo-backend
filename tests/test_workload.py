import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import RoleEnum

class WorkloadTests(unittest.TestCase):
    def tearDown(self): app.dependency_overrides.clear()

    def test_access(self):
        with TestClient(app) as c:
            self.assertEqual(c.get('/workload').status_code,401)
            for role in [RoleEnum.TECNICO,RoleEnum.ADMINISTRADOR,RoleEnum.REPORTANTE,RoleEnum.VALIDADOR]:
                user=User(id=1,name='Test',email='test@example.com',password_hash='unused')
                user.user_roles=[UserRole(user_id=1,role=role)]
                app.dependency_overrides[get_current_user]=lambda:user
                self.assertEqual(c.get('/workload').status_code,403)

    def test_aggregates(self):
        from app.db.database import SessionLocal
        from app.services.workload import summary,reports
        with SessionLocal() as db:
            result=summary(db)
            self.assertEqual(result.summary.total,sum(x.total for x in result.by_area))
            self.assertEqual(result.summary.total,sum(x.total for x in result.by_technician))
            self.assertEqual(result.summary.total,sum(x.total for x in result.by_area_and_technician))
            self.assertEqual(result.summary.total,result.summary.pending+result.summary.closed+result.summary.resolved)
            for actor in [RoleEnum.COORDINADOR,RoleEnum.RESPONSABLE_AREA]:
                user=User(id=1,name='Test',email='test@example.com',password_hash='unused')
                user.user_roles=[UserRole(user_id=1,role=actor)]
                app.dependency_overrides[get_current_user]=lambda:user
                with TestClient(app) as c:
                    self.assertEqual(c.get('/workload').status_code,200)
                    self.assertEqual(c.get('/workload/reports?limit=0').status_code,422)
                    self.assertEqual(c.get('/workload/reports?status=invalid').status_code,422)
            page=reports(db,pending_only=True,limit=2)
            self.assertLessEqual(len(page.items),2)
            self.assertEqual(page.total,result.summary.pending)
            self.assertEqual(reports(db,specialty_id=999999).total,0)
            for pair in result.by_area_and_technician:
                if pair.specialty_id and pair.assignee_id:
                    self.assertEqual(reports(db,specialty_id=pair.specialty_id,assignee_id=pair.assignee_id).total,pair.total)
