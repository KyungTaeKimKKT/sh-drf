from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from . import models

@receiver([post_save, post_delete], sender=models.Release관리)
def clear_user_cache(sender, instance, **kwargs):
    """
    User 모델이 변경되거나 삭제될 때 캐시를 초기화합니다
    """
    cache_key = 'sw_배포_list'  # 캐시 키
    cache.delete(cache_key)
