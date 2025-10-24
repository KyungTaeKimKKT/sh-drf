from django.apps import AppConfig


class 일일보고Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '일일보고'

    def ready(self):
        from . import signals  # signals.py 임포트