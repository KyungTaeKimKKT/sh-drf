from django.apps import AppConfig


class 품질경영Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '품질경영'

    def ready(self):
        import 품질경영.signals
