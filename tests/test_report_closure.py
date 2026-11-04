import unittest
from fastapi import HTTPException
from app.models.report import Report, ReportStatusEnum as Status
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import RoleEnum
from app.services.workflow import _assert_transition

class ClosureTests(unittest.TestCase):
    def actor(self, role, uid=1):
        u=User(id=uid,name='Test',email='test@example.com',password_hash='unused')
        u.user_roles=[UserRole(user_id=uid,role=role)]
        return u

    def report(self, status):
        return Report(id=1,folio='closure-test',title='Test',description='Test',campus_label='Test',space_label='Test',author_id=1,status=status)

    def test_author_cannot_reopen_closed(self):
        with self.assertRaises(HTTPException) as caught:
            _assert_transition(None,self.report(Status.CERRADA),self.actor(RoleEnum.REPORTANTE),Status.REABIERTA)
        self.assertEqual(caught.exception.status_code,403)

    def test_validator_can_reopen_closed(self):
        _assert_transition(None,self.report(Status.CERRADA),self.actor(RoleEnum.VALIDADOR,2),Status.REABIERTA)

    def test_author_can_reopen_before_closure(self):
        for status in [Status.EN_VALIDACION, Status.RESUELTA]:
            _assert_transition(None,self.report(status),self.actor(RoleEnum.REPORTANTE),Status.REABIERTA)

    def test_author_can_close_resolved(self):
        _assert_transition(None,self.report(Status.RESUELTA),self.actor(RoleEnum.REPORTANTE),Status.CERRADA)
