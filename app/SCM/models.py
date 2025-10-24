from django.db import models, transaction
from django.conf import settings



class SCM_제품(models.Model):
    """SCM 제품에 대한  모델"""
    stock_fk = models.ForeignKey('재고관리.Stock', on_delete=models.PROTECT, related_name='scms')
    상태 = models.CharField(max_length=10, choices=[('OUT', '출고'), ('IN', '입고')])
    수량 = models.DecimalField(max_digits=10, decimal_places=0)
    처리자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    생성시간 = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'SCM'
        verbose_name_plural = 'SCM 목록'