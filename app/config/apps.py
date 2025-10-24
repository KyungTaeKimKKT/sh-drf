from django.apps import AppConfig
from django.core.cache import cache

# from .clear_db_connection import clear_db_connection

class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'

    def ready(self):
        # 앱이 시작될 때 실행됩니다
        from .models import WS_URLS_DB  # 여기서 임포트하여 순환 참조 방지
        
        # DB에서 데이터를 가져와 캐시에 저장
        cache_data = list(WS_URLS_DB.objects.filter(is_active=True).values())
        cache.set('ws_urls_db', cache_data, timeout=None)  # timeout=None은 무기한 저장

        # clear_db_connection()
        # print(f"[{self.name}] DB connection cleared")