from django.urls import path
from . import views

urlpatterns = [
    path('provide/<int:response_id>/', views.provide_feedback, name='provide_feedback'),
    path('history/', views.feedback_history, name='feedback_history'),
    path('ajax-feedback/<int:response_id>/', views.ajax_feedback, name='ajax_feedback'),
    path('my-feedback/', views.my_feedback, name='my_feedback'),
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('success/', views.feedback_success, name='feedback_success'),
]