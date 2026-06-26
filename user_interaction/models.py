from django.db import models
from users.models import CustomUser

class InteractionSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    session_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"

class UserInput(models.Model):
    INPUT_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('speech', 'Speech'),
        ('emotional', 'Emotional'),
    )
    
    session = models.ForeignKey(InteractionSession, on_delete=models.CASCADE, related_name='user_inputs')
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES)
    input_data = models.TextField()
    emotional_state = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.input_type} input from {self.session.user.username}"

class AIResponse(models.Model):
    user_input = models.OneToOneField(UserInput, on_delete=models.CASCADE, related_name='ai_response')
    response_data = models.TextField()
    reasoning = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"AI Response to {self.user_input}"