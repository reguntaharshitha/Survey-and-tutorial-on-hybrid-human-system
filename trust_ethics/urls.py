from django.urls import path
from . import views

urlpatterns = [
    path('', views.trust_dashboard, name='trust_dashboard'),
    path('preferences/', views.update_trust_preferences, name='trust_preferences'),
    path('ethical-metrics/', views.ethical_metrics, name='ethical_metrics'),
    path('calibrated-confidence/', views.calibrated_confidence_api, name='calibrated_confidence_api'),
    path('admin-dashboard/', views.admin_model_dashboard, name='trust_admin_dashboard'),
]