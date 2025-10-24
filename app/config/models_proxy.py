from django.db import models
from config.models import Dummy

class RedisCacheAdmin(Dummy):
    """ 가상모델로 makemigration, migrate 할 필요 없음"""
    class Meta:
        proxy=True
        verbose_name = "Redis Cache Management"
        verbose_name_plural = "Redis Cache Management"
        # DB에 저장되지 않도록 abstract로 선언
        # managed = False
