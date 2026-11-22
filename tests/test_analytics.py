"""Isolated API and business regression tests; never touch the local MySQL data."""
import csv
import io
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.domain.attention import attention_times, elapsed_hours
from app.models.report import Report, ReportStatusEnum
from app.models.report_status_event import ReportStatusEvent
from app.models.role import RoleEnum
from app.models.user import User
from app.models.user_role import UserRole


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.author = User(id=1, name='Autor', email='author@test.com', password_hash='unused')
        self.manager = User(id=2, name='Coordinación', email='manager@test.com', password_hash='unused')
        self.tech = User(id=3, name='Técnico', email='tech@test.com', password_hash='unused')
        self.other = User(id=4, name='Otro', email='other@test.com', password_hash='unused')
        self.manager.user_roles = [UserRole(role=RoleEnum.COORDINADOR)]
        self.tech.user_roles = [UserRole(role=RoleEnum.TECNICO)]
        self.db.add_all([self.author, self.manager, self.tech, self.other])
        self.created = datetime(2026, 1, 10, 12)
        self.closed = self.add_report(1, 'cerrada', '=SUM(1,2), "prueba"\nLínea á', assignee_id=3)
        self.pending = self.add_report(2, 'reportada', 'Pendiente')
        self.reopened = self.add_report(3, 'reabierta', 'Reabierta')
        for report_id in (1, 3):
            self.event(report_id, 'en_progreso', 2)
            self.event(report_id, 'resuelta', 5)
        self.event(1, 'cerrada', 6)
        self.event(3, 'reabierta', 7)
        self.db.commit()
        app.dependency_overrides[get_db] = lambda: self.db
        self.actor = self.manager
        app.dependency_overrides[get_current_user] = lambda: self.actor
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def add_report(self, id, status, title, **kwargs):
        report = Report(id=id, folio=f'test-{id}', title=title, description='Prueba',
                        campus_label='Campus', space_label='Aula', author_id=1,
                        status=ReportStatusEnum(status), created_at=self.created, **kwargs)
        self.db.add(report)
        return report

    def event(self, report_id, status, hours):
        self.db.add(ReportStatusEvent(report_id=report_id, actor_id=2,
            from_status=ReportStatusEnum.REPORTADA, to_status=ReportStatusEnum(status),
            created_at=self.created + timedelta(hours=hours)))

    def test_summary_uses_completed_samples_only(self):
        response = self.client.get('/analytics/summary')
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data['total'], data['pending'], data['closed']), (3, 2, 1))
        self.assertEqual(data['response_hours_average'], 2)
        self.assertEqual(data['response_sample'], 2)
        self.assertEqual(data['resolution_hours_average'], 5)
        self.assertEqual(data['resolution_sample'], 1)
        self.assertEqual(data['closure_hours_average'], 6)
        self.assertIsNone(data['rating_average'])
        self.assertEqual(sum(a['total'] for a in data['by_area']), data['total'])

    def test_filter_pagination_and_export_share_results(self):
        query = '?status=cerrada&start_date=2026-01-10&end_date=2026-01-10'
        page = self.client.get('/analytics/reports' + query + '&limit=1').json()
        self.assertEqual(page['total'], 1)
        self.assertEqual(page['items'][0]['folio'], 'test-1')
        self.assertTrue(page['items'][0]['created_at'].endswith('Z'))
        self.assertEqual(self.client.get('/analytics/summary' + query).json()['total'], 1)
        response = self.client.get('/analytics/export' + query)
        self.assertIn('attachment', response.headers['content-disposition'])
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], page['items'][0]['folio'])
        self.assertTrue(rows[1][1].startswith("'=SUM"))
        self.assertIn('Línea á', rows[1][1])
        self.assertEqual(self.client.get('/analytics/reports?limit=1&offset=1').json()['items'][0]['folio'], 'test-2')

    def test_date_boundaries_and_empty_summary(self):
        for query in ('?start_date=2026-01-11', '?end_date=2026-01-09', '?campus_id=999', '?specialty_id=999', '?assignee_id=999', '?priority=alta'):
            data = self.client.get('/analytics/summary' + query).json()
            self.assertEqual(data['total'], 0)
            self.assertIsNone(data['response_hours_average'])

    def test_invalid_filters(self):
        for query in ('?start_date=2026-02-01&end_date=2026-01-01', '?status=no', '?campus_id=0', '?start_date=bad', '?limit=0', '?offset=-1', '?end_date=9999-12-31'):
            self.assertEqual(self.client.get('/analytics/reports' + query).status_code, 422, query)

    def test_management_permissions(self):
        for actor in (self.author, self.tech, self.other):
            self.actor = actor
            for path in ('/analytics/summary', '/analytics/reports', '/analytics/export'):
                self.assertEqual(self.client.get(path).status_code, 403)
        for role in (RoleEnum.COORDINADOR, RoleEnum.ADMINISTRADOR, RoleEnum.RESPONSABLE_AREA):
            self.manager.user_roles = [UserRole(role=role)]
            self.actor = self.manager
            self.assertEqual(self.client.get('/analytics/summary').status_code, 200)
        del app.dependency_overrides[get_current_user]
        self.assertEqual(self.client.get('/analytics/summary').status_code, 401)

    def test_per_incident_permissions(self):
        for actor in (self.author, self.tech, self.manager):
            self.actor = actor
            self.assertEqual(self.client.get('/reports/test-1/attention-times').status_code, 200)
            self.assertEqual(self.client.get('/reports/test-1/evaluation').status_code, 200)
        self.actor = self.other
        self.assertEqual(self.client.get('/reports/test-1/evaluation').status_code, 403)
        self.assertEqual(self.client.get('/reports/test-1/attention-times').status_code, 403)
        self.assertEqual(self.client.get('/reports/missing/evaluation').status_code, 404)

    def test_reopened_and_missing_events(self):
        reopened = self.client.get('/reports/test-3/attention-times').json()
        self.assertEqual(reopened['response_hours'], 2)
        self.assertIsNone(reopened['resolution_hours'])
        self.assertIsNotNone(reopened['open_hours'])
        self.actor = self.author
        missing = self.client.get('/reports/test-2/attention-times').json()
        self.assertIsNone(missing['response_hours'])

    def test_latest_resolution_after_reopening(self):
        self.reopened.status = ReportStatusEnum.CERRADA
        self.event(3, 'resuelta', 10)
        self.event(3, 'cerrada', 11)
        self.db.commit()
        data = self.client.get('/reports/test-3/attention-times').json()
        self.assertEqual(data['resolution_hours'], 10)
        self.assertEqual(data['closure_hours'], 11)
        self.assertIsNone(data['open_hours'])

    def test_create_evaluation_duplicate_and_summary(self):
        self.actor = self.author
        self.assertIsNone(self.client.get('/reports/test-1/evaluation').json())
        response = self.client.post('/reports/test-1/evaluation', json={'rating': 5, 'comment': '  Excelente  '})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()['comment'], 'Excelente')
        self.assertTrue(response.json()['created_at'].endswith('Z'))
        self.assertEqual(self.client.post('/reports/test-1/evaluation', json={'rating': 2}).status_code, 409)
        self.actor = self.manager
        summary = self.client.get('/analytics/summary').json()
        self.assertEqual(summary['rating_average'], 5)
        self.assertEqual(summary['evaluation_count'], 1)

    def test_evaluation_requires_author_and_closed_status(self):
        for actor in (self.manager, self.tech, self.other):
            self.actor = actor
            self.assertEqual(self.client.post('/reports/test-1/evaluation', json={'rating': 5}).status_code, 403)
        self.actor = self.author
        for folio in ('test-2', 'test-3'):
            self.assertEqual(self.client.post(f'/reports/{folio}/evaluation', json={'rating': 5}).status_code, 409)

    def test_evaluation_validation(self):
        self.actor = self.author
        for rating in (0, 6, 2.5, '5', True):
            self.assertEqual(self.client.post('/reports/test-1/evaluation', json={'rating': rating}).status_code, 422)
        self.assertEqual(self.client.post('/reports/test-1/evaluation', json={'rating': 5, 'comment': 'x' * 1001}).status_code, 422)

    def test_time_zones_and_invalid_history(self):
        aware = self.created.replace(tzinfo=timezone.utc)
        self.assertEqual(elapsed_hours(self.created, aware + timedelta(hours=2)), 2)
        self.assertIsNone(elapsed_hours(aware, aware - timedelta(hours=1)))
        self.assertIsNone(attention_times(aware, 'cerrada', None, None, None, aware)['resolution_hours'])


if __name__ == '__main__':
    unittest.main()
