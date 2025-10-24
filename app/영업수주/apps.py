from django.apps import AppConfig


class 영업수주Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '영업수주'

    def ready(self):
        import 영업수주.signal
