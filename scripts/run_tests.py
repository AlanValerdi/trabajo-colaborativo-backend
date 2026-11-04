"""Run against an explicitly configured, disposable *_test database."""
import os
import subprocess
import sys
from sqlalchemy.engine import make_url
url = os.environ.get('TEST_DATABASE_URL')
if not url or not (make_url(url).database or '').endswith('_test'):
    raise SystemExit('Set TEST_DATABASE_URL to a disposable MySQL database ending in _test')
env = dict(os.environ, SQLALCHEMY_DATABASE_URL=url, UPLOAD_DIR='/tmp/backend-test-uploads')
subprocess.run(['alembic','upgrade','head'],env=env,check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],env=env,check=True)
