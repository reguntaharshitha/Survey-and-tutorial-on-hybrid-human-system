from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('report/<int:report_id>/', views.report_detail, name='report_detail'),
    path('generate-sample/', views.generate_sample_report, name='generate_sample_report'),
    path('critical-notices/', views.critical_notices, name='critical_notices'),
]