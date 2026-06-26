"""
Verify that feedback records appear on the admin feedback review page.
Usage: python scripts/verify_feedback.py
"""
import os
import django
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from django.test import Client
from users.models import CustomUser
from feedback.models import Feedback

# Get or create superuser
admin = CustomUser.objects.filter(is_superuser=True).first()
if not admin:
    print("ERROR: No superuser found. Run create_test_feedback.py first.")
    sys.exit(1)

client = Client()
client.force_login(admin)

print(f"Total feedback records in DB: {Feedback.objects.count()}")
print(f"Feedback types: {Feedback.objects.values('feedback_type').distinct()}")

# Request the feedback review page
resp = client.get('/admin-management/feedback-review/', HTTP_HOST='127.0.0.1')
status = resp.status_code

print(f"\nGET /admin-management/feedback-review/ -> HTTP {status}")

if status == 200:
    content = resp.content.decode('utf-8', errors='replace')
    
    # Check if feedback count appears
    feedback_count = Feedback.objects.count()
    if str(feedback_count) in content:
        print(f"✓ Feedback count ({feedback_count}) is displayed on the page")
    else:
        print(f"✗ Feedback count ({feedback_count}) NOT found in page content")
    
    # Check if sample feedback text appears
    sample_comment = "Great system! Very intuitive and helpful."
    if sample_comment in content:
        print(f"✓ Sample feedback comment found in page")
    else:
        print(f"✗ Sample feedback comment NOT found in page")
        # Print a snippet of the page to debug
        print("\n--- Page content snippet (first 1500 chars) ---")
        print(content[:1500])
        print("--- end ---")
    
    # Check if "No Feedback Available" appears (would indicate empty list)
    if "No Feedback Available" in content:
        print("✗ Page shows 'No Feedback Available' - feedback not rendering")
    else:
        print("✓ Page does NOT show 'No Feedback Available' - feedback list visible")
else:
    print(f"ERROR: Got HTTP {status}, expected 200")
    print("Response content:", resp.content.decode('utf-8', errors='replace')[:500])
