import os
import sys

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.test import Client

client = Client()

print("Testing GET /accounts/register/...")
try:
    res = client.get('/accounts/register/', follow=True)
    print(f"Status Code: {res.status_code}")
    if res.status_code != 200:
        print("Response content:", res.content.decode('utf-8')[:500])
except Exception as e:
    import traceback
    print("Exception during GET /accounts/register/:")
    traceback.print_exc()