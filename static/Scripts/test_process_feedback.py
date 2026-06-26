"""
Test processing a pending feedback via admin POST to feedback_review view.
"""
import os, sys, django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()
from django.test import Client
from users.models import CustomUser
from feedback.models import Feedback

admin = CustomUser.objects.filter(is_superuser=True).first()
if not admin:
    print('No superuser found')
    sys.exit(1)

pending = Feedback.objects.filter(is_processed=False).first()
if not pending:
    # create a test feedback if none exist
    user = CustomUser.objects.filter(username='testuser').first()
    if not user:
        user = CustomUser.objects.create(username='testuser', email='test@example.com')
        user.set_password('test_pass')
        user.save()
    print('No pending feedback found — creating a test feedback')
    pending = Feedback.objects.create(
        user=user,
        feedback_type='suggestion',
        rating=4,
        comment='Auto-created test feedback',
        emotional_response='neutral',
        ai_response=None,
    )

print('Before processing: id=', pending.id, 'is_processed=', pending.is_processed)
client = Client()
client.force_login(admin)
resp = client.post('/admin-management/feedback-review/', {'feedback_id': pending.id, 'action': 'process'}, HTTP_HOST='127.0.0.1')
print('POST status', resp.status_code, resp.content)
# Refresh
pending.refresh_from_db()
print('After processing: id=', pending.id, 'is_processed=', pending.is_processed)
# Fetch the admin feedback review page and verify the rendered HTML shows the processed state
page = client.get('/admin-management/feedback-review/', HTTP_HOST='127.0.0.1')
page_text = page.content.decode('utf-8')
marker = f'data-feedback-id="{pending.id}"'
if marker in page_text:
    idx = page_text.find(marker)
    # find the end of this table row
    end_idx = page_text.find('</tr>', idx)
    if end_idx == -1:
        end_idx = idx + 3000
    snippet = page_text[idx: end_idx]
    if 'Processed' in snippet and 'status-badge' in snippet:
        print('Rendered page shows feedback as Processed')
    else:
        print('Rendered page DOES NOT show Processed for this feedback. Snippet:')
        print(snippet)
else:
    print('Rendered page does not contain the feedback row for id=', pending.id)
    # Also verify the processed metric updated
    metric_page = page_text
    import re
    proc_match = re.search(r'id="metric-processed"[^>]*>(\d+)<', metric_page)
    if proc_match:
        proc_val = int(proc_match.group(1))
        print('Processed metric on page:', proc_val)
    else:
        print('Processed metric not found on page')
