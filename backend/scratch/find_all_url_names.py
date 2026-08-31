import os
import re
import sys

sys.path.insert(0, r'c:\Users\nnava\Desktop\ClienBeat\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.urls import reverse, NoReverseMatch, get_resolver

template_dir = r'c:\Users\nnava\Desktop\ClienBeat\backend\templates\admin_panel'

url_pattern = re.compile(r"{%\s*url\s+'([^']+)'([^%]*)%}")

found_urls = set()
for root, dirs, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as fh:
                content = fh.read()
                for match in url_pattern.finditer(content):
                    url_name = match.group(1)
                    found_urls.add((url_name, f))

print("Checking all template URL names against Django reverse resolver...")
for url_name, filename in sorted(found_urls):
    # Prepare dummy args for testing resolution
    test_args = []
    if 'pk' in url_name or 'id' in url_name or 'negocio' in url_name or 'suscripcion' in url_name or 'plan' in url_name or 'rubro' in url_name:
        test_args = ['2d0c6bdc-8eb9-410e-8005-ccd46f25f2a4']
    
    # Try resolving without args, or with dummy UUID/int
    resolved = False
    for try_arg in [[], ['2d0c6bdc-8eb9-410e-8005-ccd46f25f2a4'], [1]]:
        try:
            reverse(url_name, args=try_arg)
            resolved = True
            break
        except NoReverseMatch:
            pass
        except Exception:
            resolved = True
            break
    if resolved:
        print(f"[OK] {url_name} (in {filename})")
    else:
        print(f"[FAIL NoReverseMatch] '{url_name}' used in template {filename}")
