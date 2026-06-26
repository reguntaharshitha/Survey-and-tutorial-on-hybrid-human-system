from django.db import models
from users.models import CustomUser

class TrustMetric(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=100)
    value = models.FloatField()
    confidence = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.metric_type}: {self.value} for {self.user.username}"

class EthicalAlignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    principle = models.CharField(max_length=200)
    alignment_score = models.FloatField()
    explanation = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.principle} - Alignment: {self.alignment_score}"

class MutualTrust(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ai_trust_in_user = models.FloatField()
    user_trust_in_ai = models.FloatField()
    mutual_trust_score = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Mutual Trust: {self.mutual_trust_score} with {self.user.username}"
    
    