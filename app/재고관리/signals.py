from django.db import models,transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models as 재고관리_models
import 생산관리.models as 생산관리_models
import util.utils_func as Utils

@receiver(post_save, sender=재고관리_models.Stock)
def create_stock_history(sender, instance, **kwargs):
    """재고 상태 변경 시 이력 생성"""
    try:
        # 기존 재고 정보 조회
        old_stock = 재고관리_models.Stock.objects.get(pk=instance.pk)
        

    except 재고관리_models.Stock.DoesNotExist:
        return
    