from django.urls import path
from . import views

urlpatterns = [
    # Admin Portal Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_portal_dashboard, name='admin_portal_dashboard'),
    
    # Admin Management Routes
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('user-management/', views.user_management, name='user_management'),
    path('user-details/<int:user_id>/', views.user_details, name='user_details'),
    path('ai-configuration/', views.ai_configuration, name='ai_configuration'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('feedback-review/', views.feedback_review, name='feedback_review'),
    path('security-logs/', views.security_logs, name='security_logs'),
]