from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser, UserProfile
from user_interaction.models import InteractionSession, UserInput, AIResponse
from feedback.models import Feedback
from decision_reports.models import DecisionReport, CriticalNotice
from trust_ethics.models import TrustMetric, EthicalAlignment, MutualTrust
from recommendations.models import Recommendation, AdaptiveModel
from admin_management.models import SystemConfiguration, AuditLog, PerformanceMetric
from django.contrib.admin.sites import AlreadyRegistered

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'trust_score', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'profile_picture', 'date_of_birth', 'preferences', 'trust_score')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')
    search_fields = ('user__username', 'location')

@admin.register(InteractionSession)
class InteractionSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'start_time', 'end_time')
    list_filter = ('start_time', 'user')
    search_fields = ('session_id', 'user__username')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_type', 'rating', 'timestamp', 'is_processed')
    list_filter = ('feedback_type', 'timestamp', 'is_processed')
    search_fields = ('user__username', 'comment')

@admin.register(DecisionReport)
class DecisionReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'user', 'title', 'created_at', 'is_critical')
    list_filter = ('created_at', 'is_critical')
    search_fields = ('report_id', 'user__username', 'title')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'confidence', 'is_accepted', 'is_implemented', 'created_at')
    list_filter = ('recommendation_type', 'is_accepted', 'is_implemented', 'created_at')
    search_fields = ('user__username', 'content')

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('config_key', 'last_modified', 'modified_by')
    search_fields = ('config_key', 'description')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'resource')

# Register other models
admin.site.register(UserInput)
admin.site.register(AIResponse)
admin.site.register(CriticalNotice)
# Some trust models may already be registered by `trust_ethics.admin`.
for model in (TrustMetric, EthicalAlignment, MutualTrust):
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass

admin.site.register(AdaptiveModel)
admin.site.register(PerformanceMetric)