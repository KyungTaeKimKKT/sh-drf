from django.apps import AppConfig


class 생산지시Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '생산지시'

    def ready(self):
        from . import signals  # signals.py 임포트