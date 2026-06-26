from django.db.models.signals import post_save
from django.dispatch import receiver
from user_interaction.models import AIResponse
from feedback.models import Feedback
from .models import MutualTrust
import logging
import numpy as np

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AIResponse)
def update_mutual_trust_on_ai_response(sender, instance, created, **kwargs):
    """Update MutualTrust metrics when an AI response is created or updated."""
    if not instance.user_input:
        return
    
    user = instance.user_input.session.user
    
    # Calculate average confidence from recent AI responses
    recent_responses = AIResponse.objects.filter(
        user_input__session__user=user
    ).order_by('-timestamp')[:50]
    
    confidences = [r.confidence_score for r in recent_responses if r.confidence_score]
    avg_ai_confidence = float(np.mean(confidences)) if confidences else 0.5
    
    # Get feedback to calculate user trust in AI
    recent_feedback = Feedback.objects.filter(
        user=user,
        ai_response__isnull=False
    ).order_by('-timestamp')[:50]
    
    # Count positive vs negative feedback
    positive_count = recent_feedback.filter(feedback_type='agreement').count()
    total_count = recent_feedback.count()
    
    user_trust_in_ai = (positive_count / total_count) if total_count > 0 else 0.5
    
    # AI trust in user is based on consistent positive interactions
    ai_trust_in_user = 0.5 + (0.5 * user_trust_in_ai)  # AI gains trust as user provides good feedback
    
    # Calculate mutual trust score as average
    mutual_score = (ai_trust_in_user + user_trust_in_ai) / 2
    
    # Update or create MutualTrust
    mutual_trust, created = MutualTrust.objects.get_or_create(
        user=user,
        defaults={
            'ai_trust_in_user': ai_trust_in_user,
            'user_trust_in_ai': user_trust_in_ai,
            'mutual_trust_score': mutual_score,
        }
    )
    
    if not created:
        mutual_trust.ai_trust_in_user = ai_trust_in_user
        mutual_trust.user_trust_in_ai = user_trust_in_ai
        mutual_trust.mutual_trust_score = mutual_score
        mutual_trust.save()
    
    logger.debug(f"Updated MutualTrust for user {user.username}: ai_trust={ai_trust_in_user:.2f}, user_trust={user_trust_in_ai:.2f}")


@receiver(post_save, sender=Feedback)
def update_mutual_trust_on_feedback(sender, instance, created, **kwargs):
    """Update MutualTrust metrics when feedback is submitted."""
    if not instance.user or not instance.ai_response:
        return
    
    user = instance.user
    
    # Recalculate user trust in AI based on feedback
    recent_feedback = Feedback.objects.filter(
        user=user,
        ai_response__isnull=False
    ).order_by('-timestamp')[:50]
    
    # Count positive vs negative feedback
    positive_count = recent_feedback.filter(feedback_type='agreement').count()
    total_count = recent_feedback.count()
    
    user_trust_in_ai = (positive_count / total_count) if total_count > 0 else 0.5
    
    # Get average confidence
    recent_responses = instance.ai_response.__class__.objects.filter(
        user_input__session__user=user
    ).order_by('-timestamp')[:50]
    
    confidences = [r.confidence_score for r in recent_responses if r.confidence_score]
    avg_ai_confidence = float(np.mean(confidences)) if confidences else 0.5
    
    # AI trust in user is based on consistent positive interactions
    ai_trust_in_user = 0.5 + (0.5 * user_trust_in_ai)
    
    # Calculate mutual trust score
    mutual_score = (ai_trust_in_user + user_trust_in_ai) / 2
    
    # Update or create MutualTrust
    mutual_trust, created = MutualTrust.objects.get_or_create(
        user=user,
        defaults={
            'ai_trust_in_user': ai_trust_in_user,
            'user_trust_in_ai': user_trust_in_ai,
            'mutual_trust_score': mutual_score,
        }
    )
    
    if not created:
        mutual_trust.ai_trust_in_user = ai_trust_in_user
        mutual_trust.user_trust_in_ai = user_trust_in_ai
        mutual_trust.mutual_trust_score = mutual_score
        mutual_trust.save()
    
    logger.debug(f"Updated MutualTrust for user {user.username} from feedback: ai_trust={ai_trust_in_user:.2f}, user_trust={user_trust_in_ai:.2f}")
