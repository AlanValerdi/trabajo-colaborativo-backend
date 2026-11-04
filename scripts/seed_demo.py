"""Carga demo repetible. Ejecutar con python -m scripts.seed_demo."""
from fastapi.testclient import TestClient
from sqlmodel import select
from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import RoleEnum
from app.models.specialty import Specialty, IncidentCategoryEnum
from app.core.security import hash_password

PASSWORD = 'DemoLocal2026!'
ROLES = ['administrador','coordinador','responsable_area','validador','tecnico','tecnico','reportante','reportante']

def seed():
    with SessionLocal() as db:
        for category in IncidentCategoryEnum:
            if not db.scalar(select(Specialty).where(Specialty.category == category)):
                db.add(Specialty(code=category.value.upper(), name=category.value.capitalize(), category=category))
        db.flush()
        for i, role in enumerate(ROLES):
            email = f'demo{i+1}@example.com'
            if db.scalar(select(User).where(User.email == email)):
                continue
            user = User(name=f'Demo {role} {i+1}', email=email, password_hash=hash_password(PASSWORD))
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role=RoleEnum(role)))
        db.commit()
    with TestClient(app) as client:
        def call(method, path, actor=0, **kw):
            r = client.request(method, path, headers={'Authorization':f'Bearer {tokens[actor]}'}, **kw)
            assert r.status_code < 300, (method, path, r.status_code, r.text)
            return r.json() if r.content else None
        tokens=[]
        ids=[]
        for i in range(8):
            r=client.post('/auth/login',json={'email':f'demo{i+1}@example.com','password':PASSWORD})
            assert r.status_code == 200, r.text
            tokens.append(r.json()['access_token'])
            ids.append(call('GET','/auth/me',i)['id'])
        campuses=call('GET','/campuses/')
        campus=next((x for x in campuses if x['code']=='DEMO'),None) or call('POST','/campuses/',json={'code':'DEMO','name':'Campus demostración'})
        faculties=call('GET','/faculties/')
        faculty=next((x for x in faculties if x['campusId']==campus['id']),None) or call('POST','/faculties/',json={'campusId':campus['id'],'name':'Facultad demo'})
        locations=call('GET','/locations/')
        location=next((x for x in locations if x['facultyId']==faculty['id']),None) or call('POST','/locations/',json={'facultyId':faculty['id'],'name':'Laboratorio demo'})
        specialties=call('GET','/specialties/')
        existing={r['title'] for r in call('GET','/reports/')}
        stages=['reportada','validada','asignada','en_progreso','en_validacion','resuelta','cerrada','bloqueada','reabierta','reportada','en_progreso','asignada']
        for i,target in enumerate(stages):
            title=f'[DEMO] Incidencia {i+1:02}'
            if title in existing: continue
            report=call('POST','/reports/',6,json={'title':title,'description':'Incidencia ficticia para explorar el sistema','campusId':campus['id'],'facultyId':faculty['id'],'locationId':location['id']})
            base='/reports/'+report['folio']
            call('POST',f"/reports/{report['id']}/comments",6,json={'content':'Seguimiento demo','mentions':[ids[4]]})
            if target=='reportada': continue
            call('POST',base+'/category',json={'category':specialties[i%len(specialties)]['category'],'priority':['baja','media','alta'][i%3]})
            def status(s,actor=4): return call('POST',base+'/status',actor,json={'status':s,'comment':'Seguimiento demo'})
            status('validada',2)
            if target=='validada': continue
            call('POST',base+'/assignments',json={'assigneeId':ids[4]})
            if target=='asignada': continue
            status('en_progreso')
            call('POST',base+'/diagnosis',4,json={'evaluation':'Inspección realizada','rootCause':'Desgaste de componentes'})
            call('POST',base+'/work-logs',4,json={'tasks':'Revisión y reparación','materials':'Repuestos','timeMinutes':30})
            other=next(s for s in specialties if s['category']!=specialties[i%len(specialties)]['category'])
            call('POST',base+'/collaborations',4,json={'category':other['category'],'reason':'Apoyo especializado'})
            call('POST',base+'/evidences',4,files={'file':('demo.pdf',b'%PDF-1.4\n%%EOF','application/pdf')})
            if target=='en_progreso': continue
            if target=='bloqueada': status('bloqueada'); continue
            status('en_validacion')
            if target=='en_validacion': continue
            status('resuelta')
            if target=='resuelta': continue
            status('cerrada',6)
            if target=='reabierta': status('reabierta',3)
        print('Demo disponible: demo1@example.com … demo8@example.com; contraseña:',PASSWORD)

if __name__=='__main__': seed()
