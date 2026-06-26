from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    path('', user_views.dashboard, name='home'),
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('dashboard/', user_views.dashboard, name='dashboard'),
    
    # Authentication URLs - Use custom login view that redirects admins to portal
    path('accounts/login/', user_views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_done'),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # App URLs
    path('users/', include('users.urls')),
    path('interaction/', include('user_interaction.urls')),
    path('feedback/', include('feedback.urls')),
    path('reports/', include('decision_reports.urls')),
    path('trust/', include('trust_ethics.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('admin-management/', include('admin_management.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add this for development static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)