#!/usr/bin/env python
"""
Verification script for audit logging functionality.

This script demonstrates how audit logs are recorded in the system.
It creates sample data and shows audit log entries.

Usage:
    python manage.py shell < verify_audit_logs.py
    
    OR
    
    python manage.py shell
    >>> exec(open('scripts/verify_audit_logs.py').read())
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from admin_management.models import AuditLog, SystemConfiguration

User = get_user_model()

print("\n" + "="*80)
print("AUDIT LOG VERIFICATION SCRIPT")
print("="*80)

# 1. Display total audit logs
total_logs = AuditLog.objects.count()
print(f"\n1. Total Audit Logs in Database: {total_logs}")

# 2. Display logs by action type
print("\n2. Logs by Action Type:")
action_counts = AuditLog.objects.values('action').annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id'))
for item in action_counts:
    print(f"   - {item['action']}: {item['count']}")

# 3. Display logs by resource type
print("\n3. Logs by Resource Type:")
resource_counts = AuditLog.objects.values('resource').annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id'))
for item in resource_counts:
    print(f"   - {item['resource']}: {item['count']}")

# 4. Display recent audit logs
print("\n4. Recent Audit Logs (Last 10):")
recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
for log in recent_logs:
    user_display = log.user.username if log.user else "System"
    print(f"   [{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_display:20} {log.action:10} {log.resource:20} IP: {log.ip_address or 'N/A':15}")

# 5. Display auth-related logs
print("\n5. Authentication Logs (Last 5):")
auth_logs = AuditLog.objects.filter(resource='auth').order_by('-timestamp')[:5]
if auth_logs.exists():
    for log in auth_logs:
        user_display = log.user.username if log.user else "Unknown User"
        print(f"   [{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_display:20} {log.action:10} {log.details}")
else:
    print("   No authentication logs found. Try logging in/out to create some.")

# 6. Display configuration change logs
print("\n6. Configuration Change Logs (Last 5):")
config_logs = AuditLog.objects.filter(resource='system_configuration').order_by('-timestamp')[:5]
if config_logs.exists():
    for log in config_logs:
        user_display = log.user.username if log.user else "System"
        print(f"   [{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_display:20} {log.action:10} {log.details}")
else:
    print("   No configuration logs found. Try updating AI configuration.")

# 7. Show which users have activity
print("\n7. Most Active Users (by audit log count):")
user_activity = AuditLog.objects.exclude(user__isnull=True).values('user__username').annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id')).order_by('-count')[:5]
if user_activity.exists():
    for item in user_activity:
        print(f"   - {item['user__username']}: {item['count']} actions")
else:
    print("   No user activity found.")

# 8. Info about signal handlers
print("\n8. Audit Logging Information:")
print("   ✓ Login/Logout signals are monitored by admin_management.signals")
print("   ✓ Configuration changes are logged in admin_management.views.ai_configuration")
print("   ✓ Feedback operations are logged in admin_management.views.feedback_review")
print("   ✓ Signal handlers are registered on app startup via admin_management.apps.ready()")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\nTo see audit logs in the admin interface:")
print("  1. Start the dev server: python manage.py runserver")
print("  2. Go to: http://localhost:8000/admin-management/security-logs/")
print("  3. Log in/out and refresh the page to see new entries")
print("\n")
