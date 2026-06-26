import os
import django
import sys

# Ensure project root is on sys.path so `hais_core` settings can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from django.test import Client
from users.models import CustomUser

client = Client()

# Ensure a superuser exists for testing
user = CustomUser.objects.filter(is_superuser=True).first()
if not user:
    print('No superuser found, creating temporary superuser `ci_superuser`')
    user = CustomUser.objects.create(username='ci_superuser', email='ci@example.com', is_superuser=True, is_staff=True)
    user.set_password('ci_pass')
    user.save()

client.force_login(user)

pages = [
    '/admin-management/feedback-review/',
    '/recommendations/history/',
    '/admin-management/',
    '/admin-management/user-management/',
    '/admin-management/user-details/1/',
    '/feedback/history/',
    '/feedback/submit/',
]

for p in pages:
    try:
        # Use HTTP_HOST matching ALLOWED_HOSTS to avoid DisallowedHost
        resp = client.get(p, HTTP_HOST='127.0.0.1')
        status = resp.status_code
        print(f'GET {p} -> {status}')
        if status >= 500:
            # Print a portion of the content for debugging
            content = resp.content.decode('utf-8', errors='replace')
            snippet = content[:2000]
            print('--- RESPONSE CONTENT (truncated) ---')
            print(snippet)
            print('--- END ---')
        elif status >=400:
            print('Client or server error; response length:', len(resp.content))
        else:
            print('OK')
    except Exception as e:
        print(f'Exception requesting {p}:', repr(e))
