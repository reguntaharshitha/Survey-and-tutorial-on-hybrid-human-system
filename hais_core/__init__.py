from .celery import app as celery_app

# Expose Celery app as `celery_app` for `manage.py` and other modules.
__all__ = ('celery_app',)
