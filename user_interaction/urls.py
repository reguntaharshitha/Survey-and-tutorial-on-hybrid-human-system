from django.urls import path
from . import views

urlpatterns = [
    path('', views.interaction_home, name='interaction_home'),
    path('process-text/', views.process_text_input, name='process_text_input'),
    path('process-image/', views.process_image_input, name='process_image_input'),
]