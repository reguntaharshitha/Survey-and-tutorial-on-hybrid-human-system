from django.db import models
from users.models import CustomUser
from user_interaction.models import AIResponse

class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = (
        ('agreement', 'Agreement'),
        ('correction', 'Correction'),
        ('emotional', 'Emotional'),
        ('rational', 'Rational'),
        ('suggestion', 'Suggestion'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # AI response may be absent for some free-form feedback. Make this
    # relationship optional so feedback can be recorded without a linked
    # `AIResponse` object.
    ai_response = models.ForeignKey(AIResponse, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    rating = models.IntegerField(blank=True, null=True)  # 1-5 scale
    comment = models.TextField(blank=True)
    emotional_response = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.feedback_type} feedback from {self.user.username}"