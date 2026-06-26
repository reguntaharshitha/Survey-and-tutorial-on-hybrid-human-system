from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile
from trust_ethics.models import MutualTrust
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CustomUser)
def create_user_profile_and_trust(sender, instance, created, **kwargs):
    """Create UserProfile and initial MutualTrust when a new user is created."""
    if created:
        # Create UserProfile
        UserProfile.objects.get_or_create(user=instance)
        
        # Create initial MutualTrust with default values
        MutualTrust.objects.get_or_create(
            user=instance,
            defaults={
                'ai_trust_in_user': 0.5,
                'user_trust_in_ai': 0.5,
                'mutual_trust_score': 0.5,
            }
        )
        logger.info(f"Created initial MutualTrust record for user {instance.username}")
