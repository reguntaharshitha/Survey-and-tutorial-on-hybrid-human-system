from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import AuditLog


def _get_ip_from_request(request):
    if not request:
        return None
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        # X-Forwarded-For may contain multiple IPs
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    try:
        AuditLog.objects.create(
            user=user,
            action='login',
            resource='auth',
            details={'message': 'user logged in'},
            ip_address=_get_ip_from_request(request)
        )
    except Exception:
        pass


@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    try:
        AuditLog.objects.create(
            user=user,
            action='logout',
            resource='auth',
            details={'message': 'user logged out'},
            ip_address=_get_ip_from_request(request)
        )
    except Exception:
        pass


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    try:
        username = credentials.get('username') if isinstance(credentials, dict) else str(credentials)
        AuditLog.objects.create(
            user=None,
            action='login',
            resource='auth',
            details={'message': 'failed login', 'credentials': {'username': username}},
            ip_address=_get_ip_from_request(request) if request is not None else None
        )
    except Exception:
        pass
