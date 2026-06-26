from django.db import models
from users.models import CustomUser
import uuid

class DecisionReport(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    report_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    insights = models.JSONField(default=dict, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    confidence_scores = models.JSONField(default=dict, blank=True)
    visual_data = models.JSONField(default=dict, blank=True)  # For charts and graphs
    created_at = models.DateTimeField(auto_now_add=True)
    is_critical = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = f"RPT-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Report {self.report_id} - {self.user.username}"

class CriticalNotice(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    report = models.ForeignKey(DecisionReport, on_delete=models.CASCADE, related_name='critical_notices')
    notice_type = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    message = models.TextField()
    suggested_actions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.priority} notice: {self.notice_type}"