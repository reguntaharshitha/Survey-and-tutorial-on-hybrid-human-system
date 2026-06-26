import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hais_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import CustomUser, UserProfile

def create_initial_users():
    """Create initial admin and test users"""
    User = get_user_model()
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@hais.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.create(user=admin_user)
        print("Admin user created: admin / admin123")
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@hais.com',
            'role': 'user',
            'is_staff': False,
            'is_superuser': False
        }
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        UserProfile.objects.create(user=test_user)
        print("Test user created: test_user / testpass123")
    
    # Create moderator user
    moderator_user, created = User.objects.get_or_create(
        username='moderator',
        defaults={
            'email': 'moderator@hais.com',
            'role': 'moderator',
            'is_staff': True,
            'is_superuser': False
        }
    )
    if created:
        moderator_user.set_password('mod123')
        moderator_user.save()
        UserProfile.objects.create(user=moderator_user)
        print("Moderator user created: moderator / mod123")
    
    print("Initial users created successfully!")

if __name__ == "__main__":
    create_initial_users()