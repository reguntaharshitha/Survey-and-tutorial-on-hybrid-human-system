from django.apps import AppConfig


class AdminManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_management'

    def ready(self):
        # Import signals so they are registered
        try:
            import admin_management.signals  # noqa: F401
        except Exception:
            pass
