"""Integration suite: requires an empty, migrated *_test MySQL database."""
import os
import unittest
from fastapi.testclient import TestClient
from app.main import app
from scripts.seed_demo import seed, PASSWORD

class SystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.core.config import settings
        from sqlalchemy.engine import make_url
        if not (make_url(settings.SQLALCHEMY_DATABASE_URL).database or '').endswith('_test'):
            raise RuntimeError('Tests require a dedicated *_test database')
        from app.db.database import engine
        from sqlmodel import SQLModel
        with engine.begin() as connection:
            for table in reversed(SQLModel.metadata.sorted_tables):
                connection.execute(table.delete())
        seed()
        cls.c=TestClient(app)
        cls.tokens=[]
        cls.ids=[]
        cls.seen=set()
        for i in range(8):
            r=cls.c.post('/auth/login',json={'email':f'demo{i+1}@example.com','password':PASSWORD})
            assert r.status_code==200,r.text
            cls.tokens.append(r.json())
            cls.ids.append(cls.c.get('/auth/me',headers={'Authorization':'Bearer '+r.json()['access_token']}).json()['id'])

    def req(self,method,path,actor=0,expected=200,**kw):
        r=self.c.request(method,path,headers={'Authorization':'Bearer '+self.tokens[actor]['access_token']},**kw)
        self.assertEqual(r.status_code,expected,(method,path,r.text))
        return r.json() if r.content else None

    def test_auth(self):
        self.req('GET','/health')
        self.req('POST','/auth/register',expected=201,json={'name':'Test','email':'new@example.com','password':PASSWORD})
        self.req('POST','/auth/register',expected=400,json={'name':'Test','email':'new@example.com','password':PASSWORD})
        self.req('POST','/auth/login',expected=401,json={'email':'new@example.com','password':'wrong'})
        for _ in range(2): self.req('POST','/auth/login',json={'email':'demo1@example.com','password':PASSWORD})
        self.req('POST','/auth/refresh',json={'refresh_token':self.tokens[7]['refresh_token']})
        self.req('POST','/auth/logout',7,expected=204,json={'refresh_token':self.tokens[7]['refresh_token']})
        self.req('POST','/auth/refresh',expected=401,json={'refresh_token':self.tokens[7]['refresh_token']})
        self.assertEqual(self.c.get('/auth/me').status_code,401)
        self.assertEqual(self.c.get('/auth/me',headers={'Authorization':'Bearer invalid'}).status_code,401)

    def test_users(self):
        users=self.req('GET','/users/')
        self.assertGreaterEqual(len(users),8)
        self.req('GET','/users/',6,expected=403)
        u=self.req('POST','/users/',expected=201,json={'name':'Temporary','email':'temporary@example.com','password':PASSWORD,'roles':['reportante','tecnico']})
        self.req('GET',f"/users/{u['id']}")
        self.req('PATCH',f"/users/{u['id']}/role",json={'roles':['coordinador']})
        self.req('PATCH',f"/users/{u['id']}/deactivate")
        self.req('POST','/auth/login',expected=401,json={'email':'temporary@example.com','password':PASSWORD})
        self.req('PATCH',f"/users/{u['id']}/activate")

    def test_catalogs(self):
        campus=self.req('POST','/campuses/',expected=201,json={'code':'TEST','name':'Temporary'})
        faculty=self.req('POST','/faculties/',expected=201,json={'campusId':campus['id'],'name':'Temporary'})
        loc=self.req('POST','/locations/',expected=201,json={'facultyId':faculty['id'],'name':'Temporary'})
        for path,obj in [('campuses',campus),('faculties',faculty),('locations',loc)]:
            self.req('PATCH',f"/{path}/{obj['id']}",json={'name':'Updated'})
            self.req('GET',f'/{path}/')
        self.req('GET',f"/faculties/?campusId={campus['id']}")
        self.req('GET',f"/locations/?facultyId={faculty['id']}")
        for path,obj in [('locations',loc),('faculties',faculty),('campuses',campus)]:
            self.req('DELETE',f"/{path}/{obj['id']}",expected=204)

    def test_reports_and_collaboration(self):
        reports=self.req('GET','/reports/')
        self.assertEqual(len(reports),12)
        self.assertEqual(len({r['status'] for r in reports}),9)
        for r in reports:
            base='/reports/'+r['folio']
            self.req('GET',base)
            for suffix in ['assignments','status-events','work-logs','collaborations','evidences','history','participants']:
                self.req('GET',base+'/'+suffix)
            self.req('GET',base+'/diagnosis',expected=200 if r['status'] in ['en_progreso','en_validacion','resuelta','cerrada','bloqueada','reabierta'] else 404)
            self.req('GET',f"/reports/{r['id']}/comments")
        r=next(r for r in reports if r['status']=='en_progreso')
        base='/reports/'+r['folio']
        coll=self.req('GET',base+'/collaborations')[0]
        for state in ['aceptada','completada']:
            self.req('PATCH',f"/collaborations/{coll['id']}",json={'status':state})
        self.req('PATCH',f"/collaborations/{coll['id']}",expected=409,json={'status':'aceptada'})
        self.req('POST',base+'/diagnosis',4,expected=409,json={'evaluation':'a','rootCause':'b'})
        self.req('POST',base+'/work-logs',5,expected=403,json={'tasks':'a','materials':'b','timeMinutes':1})
        self.req('POST',base+'/status',6,expected=403,json={'status':'en_validacion'})
        self.req('GET','/reports/missing',expected=404)
        self.req('GET','/activity/recent?limit=10')
        self.req('GET','/activity/recent?limit=0',expected=422)
        c=self.req('POST',f"/reports/{r['id']}/comments",6,expected=201,json={'content':'New','mentions':[self.ids[4]]})
        self.req('PUT',f"/comments/{c['id']}",6,json={'content':'Edited'})
        self.req('PUT',f"/comments/{c['id']}",5,expected=403,json={'content':'Forbidden'})
        self.req('DELETE',f"/comments/{c['id']}",6,expected=204)
        draft=next(r for r in reports if r['status']=='reportada')
        payload={k:draft[k] for k in ['title','description','campusId','facultyId','locationId']}
        self.req('PATCH','/reports/'+draft['folio'],6,json=payload)
        self.req('DELETE','/reports/'+draft['folio'],6,expected=204)

    def test_uploads(self):
        for path,mime,limit in [('/reports/images','image/png',5),('/reports/'+self.req('GET','/reports/')[3]['folio']+'/evidences','application/pdf',10)]:
            for data,ctype in [(b'','image/png'),(b'x','text/plain'),(b'x'*(limit*1024*1024+1),mime)]:
                self.req('POST',path,4,expected=400,files={'file':('test',data,ctype)})
        image=self.req('POST','/reports/images',expected=201,files={'file':('demo.png',b'fake-image','image/png')})
        from urllib.parse import urlsplit
        self.assertEqual(self.c.get(urlsplit(image['imageUrl']).path).content,b'fake-image')

if __name__=='__main__': unittest.main()
