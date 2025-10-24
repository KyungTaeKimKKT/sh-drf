from django.apps import AppConfig


class 작업지침Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '작업지침'

    def ready(self):
        from . import signals  # signals.py 임포트