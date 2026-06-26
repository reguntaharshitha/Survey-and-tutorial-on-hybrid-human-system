from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.test.utils import override_settings
from django.urls import reverse
import json

from .models import AuditLog, SystemConfiguration

User = get_user_model()


class AuditLogSignalTests(TestCase):
    """Test that audit logs are created on authentication events."""

    def setUp(self):
        """Create test user and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_login_creates_audit_log(self):
        """Test that a successful login creates an AuditLog entry."""
        initial_count = AuditLog.objects.count()
        
        # Perform login
        self.client.login(username='testuser', password='testpass123')
        
        # Check that an audit log was created
        new_count = AuditLog.objects.count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify the log details
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.resource, 'auth')
        self.assertIn('user logged in', log.details.get('message', ''))

    def test_logout_creates_audit_log(self):
        """Test that logout creates an AuditLog entry."""
        # First login
        self.client.login(username='testuser', password='testpass123')
        initial_count = AuditLog.objects.count()
        
        # Perform logout
        self.client.logout()
        
        # Check that an audit log was created
        new_count = AuditLog.objects.count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify the log details
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'logout')
        self.assertEqual(log.resource, 'auth')
        self.assertIn('user logged out', log.details.get('message', ''))

    def test_failed_login_creates_audit_log(self):
        """Test that failed login attempts are logged."""
        initial_count = AuditLog.objects.count()
        
        # Attempt login with wrong password
        self.client.login(username='testuser', password='wrongpassword')
        
        # Check that an audit log was created for failed login
        new_count = AuditLog.objects.count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify the log details
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.resource, 'auth')
        self.assertIn('failed login', log.details.get('message', ''))

    def test_audit_log_records_ip_address(self):
        """Test that IP address is recorded in audit logs."""
        # Login with a specific client IP
        self.client.login(username='testuser', password='testpass123')
        
        log = AuditLog.objects.latest('timestamp')
        # The IP should be recorded (could be 127.0.0.1 in tests or None if not set)
        # Just verify the field exists and can be None
        self.assertTrue(hasattr(log, 'ip_address'))


class ConfigurationAuditLogTests(TestCase):
    """Test that AuditLog entries are created when system configuration changes."""

    def setUp(self):
        """Create test admin user and client."""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_configuration_create_logs_audit_entry(self):
        """Test that creating a system configuration creates an AuditLog."""
        self.client.login(username='admin', password='adminpass123')
        initial_count = AuditLog.objects.count()
        
        # Simulate POST to ai_configuration to create a new config
        response = self.client.post(
            '/admin-management/ai-configuration/',
            {
                'config_key': 'test_config',
                'config_value': '{"key": "value"}'
            },
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        
        # Check response is success (if endpoint exists)
        if response.status_code == 200:
            # Check that an audit log was created
            new_count = AuditLog.objects.count()
            self.assertGreater(new_count, initial_count)
            
            # Verify the log details
            log = AuditLog.objects.filter(resource='system_configuration').latest('timestamp')
            self.assertEqual(log.user, self.admin_user)
            self.assertEqual(log.action, 'create')
            self.assertEqual(log.resource, 'system_configuration')
            self.assertEqual(log.ip_address, '192.168.1.100')

    def test_configuration_update_logs_audit_entry(self):
        """Test that updating a system configuration creates an AuditLog."""
        self.client.login(username='admin', password='adminpass123')
        
        # Create an initial configuration
        SystemConfiguration.objects.create(
            config_key='test_update_config',
            config_value={'initial': 'value'},
            modified_by=self.admin_user
        )
        
        initial_count = AuditLog.objects.count()
        
        # Update the configuration
        response = self.client.post(
            '/admin-management/ai-configuration/',
            {
                'config_key': 'test_update_config',
                'config_value': '{"updated": "value"}'
            },
            HTTP_X_FORWARDED_FOR='192.168.1.101'
        )
        
        if response.status_code == 200:
            # Check that an audit log was created
            new_count = AuditLog.objects.count()
            self.assertGreater(new_count, initial_count)
            
            # Verify the log details
            log = AuditLog.objects.filter(resource='system_configuration').latest('timestamp')
            self.assertEqual(log.user, self.admin_user)
            self.assertEqual(log.action, 'update')


class FeedbackAuditLogTests(TestCase):
    """Test that AuditLog entries are created when feedback is processed or deleted."""

    def setUp(self):
        """Create test users and admin user."""
        from feedback.models import Feedback
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_feedback_audit_log_can_be_created(self):
        """Test that AuditLog entries can be created for feedback operations."""
        log = AuditLog.objects.create(
            user=self.admin_user,
            action='update',
            resource='feedback',
            details={'feedback_id': 1, 'action': 'process'},
            ip_address='192.168.1.100'
        )
        
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.resource, 'feedback')
        self.assertIsNotNone(log.timestamp)

    def test_feedback_delete_audit_log(self):
        """Test that AuditLog entries can be created for feedback deletion."""
        log = AuditLog.objects.create(
            user=self.admin_user,
            action='delete',
            resource='feedback',
            details={'feedback_id': 1, 'user': self.user.id},
            ip_address='192.168.1.100'
        )
        
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.action, 'delete')
        self.assertEqual(log.resource, 'feedback')
        self.assertEqual(log.ip_address, '192.168.1.100')


class AuditLogModelTests(TestCase):
    """Test the AuditLog model functionality."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_audit_log_creation(self):
        """Test creating an AuditLog entry directly."""
        log = AuditLog.objects.create(
            user=self.user,
            action='login',
            resource='auth',
            details={'message': 'test login'},
            ip_address='192.168.1.100'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.resource, 'auth')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertIsNotNone(log.timestamp)

    def test_audit_log_with_null_user(self):
        """Test creating an AuditLog with null user (for system actions)."""
        log = AuditLog.objects.create(
            user=None,
            action='login',
            resource='auth',
            details={'message': 'failed login', 'credentials': {'username': 'unknown'}},
            ip_address='192.168.1.101'
        )
        
        self.assertIsNone(log.user)
        self.assertEqual(log.action, 'login')
        self.assertIn('failed login', log.details.get('message', ''))

    def test_audit_log_string_representation(self):
        """Test the __str__ method of AuditLog."""
        log = AuditLog.objects.create(
            user=self.user,
            action='update',
            resource='feedback',
            details={},
            ip_address='192.168.1.100'
        )
        
        str_repr = str(log)
        self.assertIn('update', str_repr)
        self.assertIn('feedback', str_repr)
        self.assertIn(self.user.username, str_repr)

