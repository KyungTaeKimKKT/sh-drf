from django.apps import AppConfig


class ReleaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'release'

    def ready(self):
        from . import signals  # signals.py 임포트