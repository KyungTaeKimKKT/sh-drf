from django.db import models
from django.conf import settings

from django.utils import timezone
from datetime import datetime

# from 생산관리.models import (
#     생산계획_확정_Branch,
# )


class SerialDB(models.Model):
    serial = models.CharField(max_length=30, unique=True, blank=True, null=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now )
    확정자 = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    확정Branch_fk = models.ForeignKey('생산관리.생산계획_확정Branch', on_delete=models.CASCADE, blank=True, null=True)
    ProductionLine_fk = models.ForeignKey('생산관리.ProductionLine', on_delete=models.SET_NULL, null=True)

class SerialHistory(models.Model):
    serial_fk = models.ForeignKey(SerialDB, on_delete=models.CASCADE, related_name='histories')
    # 생산실적_fk = models.ForeignKey('생산관리.생산실적', on_delete=models.CASCADE, blank=True, null=True )
    스캔시간 = models.DateTimeField(auto_now_add=True)
    스캔유형 = models.CharField(max_length=10, choices=[('IN', '투입'), ('OUT', '완료')])
    작업자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    ProductionLine_fk = models.ForeignKey('생산관리.ProductionLine', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['스캔시간']


