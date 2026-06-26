from django.apps import AppConfig


class TrustEthicsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trust_ethics'
    
    def ready(self):
        import trust_ethics.signals
