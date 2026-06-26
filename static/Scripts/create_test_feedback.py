"""
Generate sample feedback records for testing the feedback review page.
Usage: python scripts/create_test_feedback.py
"""
''''
import os
import django
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from feedback.models import Feedback
from users.models import CustomUser
from django.utils import timezone

# Ensure a superuser exists
admin_user = CustomUser.objects.filter(is_superuser=True).first()
if not admin_user:
    print("Creating superuser for testing...")
    admin_user = CustomUser.objects.create(
        username='admin_test',
        email='admin@test.com',
        is_superuser=True,
        is_staff=True
    )
    admin_user.set_password('admin_pass')
    admin_user.save()

# Ensure a regular user exists
regular_user = CustomUser.objects.filter(username='testuser', is_superuser=False).first()
if not regular_user:
    print("Creating regular user for testing...")
    regular_user = CustomUser.objects.create(
        username='testuser',
        email='test@example.com',
        is_superuser=False,
        is_staff=False
    )
    regular_user.set_password('test_pass')
    regular_user.save()

# Create sample feedback records
sample_feedback = [
    {
        'user': regular_user,
        'feedback_type': 'agreement',
        'rating': 5,
        'comment': 'Great system! Very intuitive and helpful.',
        'emotional_response': 'positive'
    },
    {
        'user': regular_user,
        'feedback_type': 'suggestion',
        'rating': 4,
        'comment': 'Could use more customization options in the dashboard.',
        'emotional_response': 'neutral'
    },
    {
        'user': regular_user,
        'feedback_type': 'correction',
        'rating': 3,
        'comment': 'Some of the recommendations seemed off-topic.',
        'emotional_response': 'neutral'
    },
    {
        'user': regular_user,
        'feedback_type': 'rational',
        'rating': 4,
        'comment': 'The logic is solid but response time could be faster.',
        'emotional_response': 'neutral'
    },
    {
        'user': regular_user,
        'feedback_type': 'emotional',
        'rating': 5,
        'comment': 'Really appreciate how the system understands context.',
        'emotional_response': 'positive'
    },
]

created_count = 0
for fb_data in sample_feedback:
    feedback = Feedback.objects.create(
        **fb_data,
        ai_response=None,  # No linked AIResponse for this test data
    )
    created_count += 1
    print(f"✓ Created feedback: {feedback.feedback_type} from {feedback.user.username}")

print(f"\nTotal feedback records created: {created_count}")
print(f"Visit admin page: http://127.0.0.1:8000/admin-management/feedback-review/")
print(f"Log in with superuser: admin_test / admin_pass")
'''''