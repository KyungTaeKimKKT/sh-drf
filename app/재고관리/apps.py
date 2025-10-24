from django.apps import AppConfig


class 재고관리Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '재고관리'

    def ready(self):
        import 재고관리.signals
