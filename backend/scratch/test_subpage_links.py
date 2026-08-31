import os
import sys

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client

client = Client()
res = client.get('/legal/privacy/')
assert res.status_code == 200
assert b'/#caracteristicas' in res.content
assert b'/#precios' in res.content
print("[OK] Subpage navbar links point to /#caracteristicas and /#precios absolute paths!")
