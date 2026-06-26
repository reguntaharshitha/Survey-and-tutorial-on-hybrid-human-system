"""
Verify that feedback submitted by users appears in both:
1. User feedback history page: /feedback/history/
2. Admin feedback review page: /admin-management/feedback-review/
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

print("=" * 60)
print("FEEDBACK VISIBILITY TEST")
print("=" * 60)

# Get or create users
admin = CustomUser.objects.filter(is_superuser=True).first()
if not admin:
    print("ERROR: No superuser found")
    sys.exit(1)

regular_user = CustomUser.objects.filter(username='testuser', is_superuser=False).first()
if not regular_user:
    print("ERROR: No regular user found. Run create_test_feedback.py first")
    sys.exit(1)

# Get regular user's feedback from database
user_feedback_count = Feedback.objects.filter(user=regular_user).count()
print(f"\n📊 Database: {user_feedback_count} feedback records for user '{regular_user.username}'")

if user_feedback_count == 0:
    print("⚠️  No feedback found in database for this user")
else:
    sample_feedback = Feedback.objects.filter(user=regular_user).first()
    print(f"   Sample: {sample_feedback.comment[:50]}...")

# Test 1: Check user's feedback history page
print("\n" + "=" * 60)
print("TEST 1: User Feedback History Page (/feedback/history/)")
print("=" * 60)

client = Client()
client.force_login(regular_user)
resp = client.get('/feedback/history/', HTTP_HOST='127.0.0.1')
print(f"Status: HTTP {resp.status_code}")

if resp.status_code == 200:
    content = resp.content.decode('utf-8', errors='replace')
    
    # Check if feedback count appears
    if str(user_feedback_count) in content:
        print(f"✅ Feedback count ({user_feedback_count}) is displayed")
    else:
        print(f"❌ Feedback count ({user_feedback_count}) NOT displayed")
    
    # Check if sample feedback appears
    if sample_feedback and sample_feedback.comment[:20] in content:
        print(f"✅ Sample feedback comment appears in page")
    else:
        print(f"❌ Sample feedback comment NOT found in page")
    
    # Check if "No Feedback" message appears
    if "No Feedback Submitted Yet" in content:
        print("❌ Page shows 'No Feedback Submitted Yet' - user feedback not rendering")
    else:
        print("✅ Page does NOT show 'No Feedback Submitted Yet'")
else:
    print(f"❌ ERROR: Got HTTP {resp.status_code}, expected 200")

# Test 2: Check admin feedback review page
print("\n" + "=" * 60)
print("TEST 2: Admin Feedback Review Page (/admin-management/feedback-review/)")
print("=" * 60)

client2 = Client()
client2.force_login(admin)
resp2 = client2.get('/admin-management/feedback-review/', HTTP_HOST='127.0.0.1')
print(f"Status: HTTP {resp2.status_code}")

total_feedback = Feedback.objects.count()
print(f"Total feedback in database: {total_feedback}")

if resp2.status_code == 200:
    content2 = resp2.content.decode('utf-8', errors='replace')
    
    # Check if total feedback count appears
    if str(total_feedback) in content2:
        print(f"✅ Total feedback count ({total_feedback}) is displayed")
    else:
        print(f"❌ Total feedback count ({total_feedback}) NOT displayed")
    
    # Check if user's feedback appears
    if sample_feedback and sample_feedback.comment[:20] in content2:
        print(f"✅ User's feedback comment appears in admin page")
    else:
        print(f"❌ User's feedback comment NOT found in admin page")
    
    # Check if "No Feedback Available" message appears
    if "No Feedback Available" in content2:
        print("❌ Page shows 'No Feedback Available' - feedback not rendering")
    else:
        print("✅ Page does NOT show 'No Feedback Available'")
else:
    print(f"❌ ERROR: Got HTTP {resp2.status_code}, expected 200")

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("✅ All checks should show green checkmarks")
print("If any show red X, feedback visibility is broken")
print("=" * 60)
