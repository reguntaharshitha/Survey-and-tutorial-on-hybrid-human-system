from django.core.management.base import BaseCommand
from users.models import CustomUser
from trust_ethics.models import MutualTrust
from user_interaction.models import AIResponse
from feedback.models import Feedback
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize MutualTrust records for existing users'

    def add_arguments(self, parser):
        parser.add_argument('--recalculate', action='store_true', help='Recalculate metrics for all users')

    def handle(self, *args, **options):
        recalculate = options.get('recalculate', False)
        
        users = CustomUser.objects.all()
        created_count = 0
        updated_count = 0
        
        for user in users:
            # Check if MutualTrust already exists
            mutual_trust = MutualTrust.objects.filter(user=user).first()
            
            if mutual_trust and not recalculate:
                self.stdout.write(f"Skipping {user.username} - MutualTrust already exists")
                continue
            
            # Calculate metrics
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
            
            positive_count = sum(1 for fb in recent_feedback if fb.feedback_type == 'agreement')
            total_count = len(recent_feedback)
            
            user_trust_in_ai = (positive_count / total_count) if total_count > 0 else 0.5
            
            # AI trust in user
            ai_trust_in_user = 0.5 + (0.5 * user_trust_in_ai)
            
            # Mutual trust score
            mutual_score = (ai_trust_in_user + user_trust_in_ai) / 2
            
            if mutual_trust:
                # Update existing
                mutual_trust.ai_trust_in_user = ai_trust_in_user
                mutual_trust.user_trust_in_ai = user_trust_in_ai
                mutual_trust.mutual_trust_score = mutual_score
                mutual_trust.save()
                updated_count += 1
                self.stdout.write(f"Updated MutualTrust for {user.username}: ai_trust={ai_trust_in_user:.2f}, user_trust={user_trust_in_ai:.2f}")
            else:
                # Create new
                MutualTrust.objects.create(
                    user=user,
                    ai_trust_in_user=ai_trust_in_user,
                    user_trust_in_ai=user_trust_in_ai,
                    mutual_trust_score=mutual_score,
                )
                created_count += 1
                self.stdout.write(f"Created MutualTrust for {user.username}: ai_trust={ai_trust_in_user:.2f}, user_trust={user_trust_in_ai:.2f}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} and updated {updated_count} MutualTrust records'
            )
        )
