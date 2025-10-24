from django.db import models,transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from . import models as Models_DB
# import 생산관리.models
import util.utils_func as Utils

from django.core.cache import cache
from datetime import datetime, date,time, timedelta

# 캐시 키 상수 정의
휴일등록_CACHE_KEY = '일일보고_휴일등록_LIST'


@receiver([post_save, post_delete], sender=Models_DB.휴일_DB )
def clear_휴일_DB_cache(sender, instance, **kwargs):
    """모델이 변경되거나 삭제될 때 캐시를 초기화합니다"""
    cache.delete(휴일등록_CACHE_KEY)

	### 3일 cache도 delete
    today = datetime.now().date()
    cache_key = f'three_days_list_{today}'
    cache.delete(cache_key)

# @receiver([post_save, post_delete], sender=Models_DB.생산계획_DDay )
# def clear_생산계획_DDay_cache(sender, instance, **kwargs):
#     """모델이 변경되거나 삭제될 때 캐시를 초기화합니다"""
#     cache.delete(생산관리_생산계획_DDay_CACHE_KEY)