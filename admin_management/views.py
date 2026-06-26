from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils.decorators import method_decorator
from users.models import CustomUser
from feedback.models import Feedback
from user_interaction.models import InteractionSession
from .models import AuditLog, PerformanceMetric, SystemConfiguration
from .forms import AdminLoginForm
import json
from django.db import models
from user_interaction.models import UserInput
from django.db.models import Count, Q


def admin_required(user):
    # Allow explicit role-based admins/moderators, or Django staff/superusers.
    if not user.is_authenticated:
        return False
    if getattr(user, 'role', None) in ['admin', 'moderator']:
        return True
    # Allow users with Django staff/superuser flags as admins
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    return False


def admin_only(user):
    """Return True only for full administrators (role 'admin' or staff/superuser).

    This prevents users with role 'moderator' from accessing admin-only pages
    such as user management and security logs.
    """
    if not user.is_authenticated:
        return False
    if getattr(user, 'role', None) == 'admin':
        return True
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    return False


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Special login for admin/superuser access"""
    # If already logged in as admin, redirect to dashboard
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_portal_dashboard')
        else:
            # Regular user logged in, they need to logout first
            return redirect('logout')
    
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            # Log the admin login
            try:
                ip = get_client_ip(request)
                AuditLog.objects.create(
                    user=user,
                    action='login',
                    resource='admin_portal',
                    details={'login_type': 'admin_portal'},
                    ip_address=ip
                )
            except Exception as e:
                pass  # Don't fail if audit logging fails
            
            login(request, user)
            messages.success(request, f'Welcome back, Admin {user.username}!')
            
            # Redirect to next or admin dashboard
            next_url = request.POST.get('next', request.GET.get('next', 'admin_portal_dashboard'))
            return redirect(next_url)
        else:
            # Log failed login attempts
            username = request.POST.get('username', 'unknown')
            try:
                ip = get_client_ip(request)
                AuditLog.objects.create(
                    user=None,
                    action='login',
                    resource='admin_portal',
                    details={'login_type': 'admin_portal', 'status': 'failed', 'username': username},
                    ip_address=ip
                )
            except Exception as e:
                pass
            
            messages.error(request, 'Invalid admin credentials or insufficient permissions.')
    else:
        form = AdminLoginForm()
    
    context = {
        'form': form,
        'next': request.GET.get('next', ''),
    }
    
    return render(request, 'admin_management/admin_login.html', context)


@login_required
@user_passes_test(admin_required)
def admin_logout(request):
    """Admin logout"""
    if request.user.is_authenticated:
        try:
            ip = get_client_ip(request)
            AuditLog.objects.create(
                user=request.user,
                action='logout',
                resource='admin_portal',
                details={'logout_type': 'admin_portal'},
                ip_address=ip
            )
        except Exception as e:
            pass
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')


def admin_login_required(view_func):
    """Decorator that requires admin login and redirects to admin login page"""
    @login_required(login_url='admin_login')
    @user_passes_test(admin_required, login_url='admin_login')
    def wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped_view


@admin_login_required
def admin_portal_dashboard(request):
    """Admin portal dashboard with operation tracking"""
    # System statistics
    total_users = CustomUser.objects.count()
    active_sessions = InteractionSession.objects.filter(end_time__isnull=True).count()
    total_feedback = Feedback.objects.count()
    processed_feedback = Feedback.objects.filter(is_processed=True).count()
    
    # Admin-specific operations tracking
    today_logins = AuditLog.objects.filter(
        action='login',
        resource='admin_portal'
    ).count()
    
    today_operations = AuditLog.objects.filter(
        resource__in=['system_configuration', 'feedback', 'user_management']
    ).count()
    
    # Get admin user actions today
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    admin_logs = AuditLog.objects.filter(
        timestamp__date=today,
        user__isnull=False
    ).select_related('user').order_by('-timestamp')[:20]
    
    # Performance metrics
    performance_metrics = PerformanceMetric.objects.order_by('-timestamp')[:10]
    
    # Recent system activity
    recent_logs = AuditLog.objects.order_by('-timestamp')[:15]
    
    # User operations stats
    recent_users_active = InteractionSession.objects.filter(
        start_time__gte=timezone.now() - timedelta(hours=24)
    ).values('user').distinct().count()
    
    # Recent registrations
    recent_registrations = CustomUser.objects.filter(
        date_joined__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    context = {
        'total_users': total_users,
        'active_sessions': active_sessions,
        'total_feedback': total_feedback,
        'processed_feedback': processed_feedback,
        'today_logins': today_logins,
        'today_operations': today_operations,
        'admin_logs': admin_logs,
        'performance_metrics': performance_metrics,
        'recent_logs': recent_logs,
        'recent_users_active': recent_users_active,
        'recent_registrations': recent_registrations,
    }
    
    return render(request, 'admin_management/admin_portal_dashboard.html', context)


@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    # System statistics
    total_users = CustomUser.objects.count()
    active_sessions = InteractionSession.objects.filter(end_time__isnull=True).count()
    total_feedback = Feedback.objects.count()
    processed_feedback = Feedback.objects.filter(is_processed=True).count()
    
    # Performance metrics
    performance_metrics = PerformanceMetric.objects.order_by('-timestamp')[:10]
    
    # Recent audit logs
    recent_logs = AuditLog.objects.order_by('-timestamp')[:10]
    
    context = {
        'total_users': total_users,
        'active_sessions': active_sessions,
        'total_feedback': total_feedback,
        'processed_feedback': processed_feedback,
        'performance_metrics': performance_metrics,
        'recent_logs': recent_logs,
    }
    
    return render(request, 'admin_management/dashboard.html', context)

@login_required
@user_passes_test(admin_only)
def user_management(request):
    """User management with audit logging for admin actions"""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            target_user = CustomUser.objects.get(id=user_id)
            ip = get_client_ip(request)
            
            if action == 'deactivate':
                target_user.is_active = False
                target_user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource='user_management',
                    details={'target_user': target_user.id, 'action': 'deactivate'},
                    ip_address=ip
                )
                messages.success(request, f'User {target_user.username} has been deactivated.')
            
            elif action == 'activate':
                target_user.is_active = True
                target_user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource='user_management',
                    details={'target_user': target_user.id, 'action': 'activate'},
                    ip_address=ip
                )
                messages.success(request, f'User {target_user.username} has been activated.')
            
            elif action == 'grant_staff':
                target_user.is_staff = True
                target_user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource='user_management',
                    details={'target_user': target_user.id, 'action': 'grant_staff'},
                    ip_address=ip
                )
                messages.success(request, f'{target_user.username} promoted to staff.')
            
            elif action == 'revoke_staff':
                target_user.is_staff = False
                target_user.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource='user_management',
                    details={'target_user': target_user.id, 'action': 'revoke_staff'},
                    ip_address=ip
                )
                messages.success(request, f'Removed staff privileges from {target_user.username}.')
            
            elif action == 'delete':
                username = target_user.username
                target_user.delete()
                AuditLog.objects.create(
                    user=request.user,
                    action='delete',
                    resource='user_management',
                    details={'target_user_id': user_id, 'username': username},
                    ip_address=ip
                )
                messages.success(request, f'User {username} has been deleted.')
        
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    # Log admin access to this page
    try:
        ip = get_client_ip(request)
        AuditLog.objects.create(
            user=request.user,
            action='access',
            resource='user_management',
            details={'action': 'view'},
            ip_address=ip
        )
    except Exception:
        pass
    
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'admin_management/user_management.html', {'users': users})

@login_required
@user_passes_test(admin_required)
def ai_configuration(request):
    configurations = SystemConfiguration.objects.all()
    
    if request.method == 'POST':
        config_key = request.POST.get('config_key')
        config_value = request.POST.get('config_value')
        
        try:
            config_value = json.loads(config_value)
        except:
            config_value = config_value
        
        config, created = SystemConfiguration.objects.update_or_create(
            config_key=config_key,
            defaults={
                'config_value': config_value,
                'modified_by': request.user
            }
        )
        # Record audit log for configuration change
        try:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            AuditLog.objects.create(
                user=request.user,
                action='update' if not created else 'create',
                resource='system_configuration',
                details={'config_key': config_key, 'created': created},
                ip_address=ip
            )
        except Exception:
            pass
        
        return JsonResponse({'success': True})
    
    return render(request, 'admin_management/ai_configuration.html', {'configurations': configurations})

@login_required
@user_passes_test(admin_required)
def analytics_dashboard(request):
    # Analytics data
    user_registrations = CustomUser.objects.extra(
        select={'date': 'DATE(date_joined)'}
    ).values('date').annotate(count=models.Count('id'))
    
    interaction_data = UserInput.objects.extra(
        select={'date': 'DATE(timestamp)'}
    ).values('date').annotate(count=models.Count('id'))
    
    feedback_ratings = Feedback.objects.values('rating').annotate(count=models.Count('id'))
    
    context = {
        'user_registrations': list(user_registrations),
        'interaction_data': list(interaction_data),
        'feedback_ratings': list(feedback_ratings),
    }
    
    return render(request, 'admin_management/analytics.html', context)

@login_required
@user_passes_test(admin_required)
def feedback_review(request):
    feedbacks = Feedback.objects.select_related('user', 'ai_response').order_by('-timestamp')

    if request.method == 'POST':
        feedback_id = request.POST.get('feedback_id')
        action = request.POST.get('action')

        feedback = Feedback.objects.get(id=feedback_id)

        if action == 'process':
            feedback.is_processed = True
            feedback.save()
            # Audit log
            try:
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    resource='feedback',
                    details={'feedback_id': feedback_id, 'action': 'process'},
                    ip_address=ip
                )
            except Exception:
                pass
        elif action == 'delete':
            # Capture details before delete
            try:
                details = {'feedback_id': feedback_id, 'user': feedback.user.id}
            except Exception:
                details = {'feedback_id': feedback_id}
            feedback.delete()
            try:
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
                AuditLog.objects.create(
                    user=request.user,
                    action='delete',
                    resource='feedback',
                    details=details,
                    ip_address=ip
                )
            except Exception:
                pass

        return JsonResponse({'success': True})

    # Compute summary metrics for the template
    total = feedbacks.count()
    processed_count = feedbacks.filter(is_processed=True).count()
    pending_count = total - processed_count
    # Average rating (safe fallback to 0)
    avg_rating = feedbacks.aggregate(avg=models.Avg('rating')).get('avg') or 0
    agreement_count = feedbacks.filter(feedback_type='agreement').count()
    correction_count = feedbacks.filter(feedback_type='correction').count()

    context = {
        'feedbacks': feedbacks,
        'total_feedback': total,
        'processed_feedback_count': processed_count,
        'pending_feedback_count': pending_count,
        'avg_feedback_rating': avg_rating,
        'agreement_count': agreement_count,
        'correction_count': correction_count,
    }

    return render(request, 'admin_management/feedback_review.html', context)

@login_required
@user_passes_test(admin_only)
def security_logs(request):
    """Security logs with filtering and audit tracking"""
    # Log this access
    try:
        ip = get_client_ip(request)
        AuditLog.objects.create(
            user=request.user,
            action='access',
            resource='security_logs',
            details={'action': 'view'},
            ip_address=ip
        )
    except Exception:
        pass
    
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters if provided
    action_filter = request.GET.get('action')
    resource_filter = request.GET.get('resource')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if resource_filter:
        logs = logs.filter(resource=resource_filter)
    
    # Get unique actions and resources for filter dropdowns
    unique_actions = AuditLog.objects.values_list('action', flat=True).distinct()
    unique_resources = AuditLog.objects.values_list('resource', flat=True).distinct()
    
    context = {
        'logs': logs,
        'unique_actions': unique_actions,
        'unique_resources': unique_resources,
        'selected_action': action_filter,
        'selected_resource': resource_filter,
    }
    return render(request, 'admin_management/security_logs.html', context)

@login_required
@user_passes_test(admin_only)
def user_details(request, user_id):
    """Display detailed user information and interaction history for admin review."""
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        raise Http404(f"User with ID {user_id} not found")
    
    # Log this admin access
    try:
        ip = get_client_ip(request)
        AuditLog.objects.create(
            user=request.user,
            action='access',
            resource='user_details',
            details={'target_user': user_id},
            ip_address=ip
        )
    except Exception:
        pass
    
    # Fetch user's feedback
    user_feedback = Feedback.objects.filter(user=user).order_by('-timestamp')
    
    # Fetch user's interaction sessions
    user_sessions = InteractionSession.objects.filter(user=user).order_by('-start_time')[:10]
    
    # Count user statistics
    from django.db.models import Count
    total_interactions = InteractionSession.objects.filter(user=user).count()
    total_feedback = user_feedback.count()
    
    context = {
        'user': user,
        'user_feedback': user_feedback,
        'user_sessions': user_sessions,
        'total_interactions': total_interactions,
        'total_feedback': total_feedback,
    }
    
    return render(request, 'admin_management/user_details.html', context)