from django.apps import AppConfig


class 영업MboConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '영업mbo'

    # def ready(self):
    #     from . import signals  # signals.py 임포트