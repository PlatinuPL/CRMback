from django.apps import AppConfig

class CrmModuleOneConfig(AppConfig):  # <- z wielkich liter, zgodnie z nazwą aplikacji
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'CrmModuleOne'

    def ready(self):
        import CrmModuleOne.signals
