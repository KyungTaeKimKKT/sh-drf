from django.db import models, transaction
from django.conf import settings
from django.core.validators import MinValueValidator

from 생산관리 import models as 생산관리_models
from SCM import models as SCM_models

class Warehouse(models.Model):
    """창고 정보 모델"""
    WAREHOUSE_CHOICES = [
        ('WH20', 'HI 창고'),
        ('WH30', 'PG 창고'),
        ('WH40', 'PO 창고'),
    ]
    
    창고코드 = models.CharField(max_length=4, choices=WAREHOUSE_CHOICES, unique=True, verbose_name='창고 코드')
    창고명 = models.CharField(max_length=50, verbose_name='창고명')
    창고설명 = models.TextField(blank=True, verbose_name='설명')
    
    class Meta:
        verbose_name = '창고'
        verbose_name_plural = '창고 목록'

class Stock(models.Model):
    """재고 관리 모델"""
    STATUS_CHOICES = [
        ('IN-READY', '입고대기'),
        ('IN', '입고'),
        ('OUT', '출고'),
        ('OUT-READY', '출고대기'),
    ]
    
    생산관리_제품완료_fk = models.ForeignKey('생산관리.생산관리_제품완료', on_delete=models.PROTECT, null=True, blank=True)
    창고_fk = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True)
    상태 = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    수량 = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)] )
    처리시간 = models.DateTimeField(null=True, blank=True )
    Proj_No = models.CharField(max_length=50, blank=True)
    비고 = models.TextField(blank=True , null=True )
    생성시간 = models.DateTimeField(auto_now_add=True )
    is_active = models.BooleanField(default=True )  # 출고 처리된 경우 False
    처리자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True )

    출고처_fk = models.ForeignKey('생산관리.판금처_DB', on_delete=models.PROTECT, null=True, blank=True )

    class Meta:
        verbose_name = '재고'
        verbose_name_plural = '재고 목록'

    @transaction.atomic
    def 입고대기_생성(self, _obj: 생산관리_models.생산관리_제품완료, 창고_fk: int):
        """관련된 공정상세들의 완료 처리"""
        self.생산관리_제품완료_fk = _obj
        self.창고_fk = Warehouse.objects.get(id=창고_fk)
        self.상태 = 'IN-READY'
        self.수량 = _obj.실적수량
        self.처리시간 = _obj.완료일시
        self.Proj_No = _obj.Proj_No
        self.비고 = _obj.비고
        self.save()

    @transaction.atomic
    def 출고_처리(self, 새로운_상태: str):
        """상태 변경 및 SCM 생성"""
        if 새로운_상태 not in ['IN', 'OUT']:
            raise ValueError("상태는 'IN' 또는 'OUT'이어야 합니다.")
        
        이전상태 = self.상태
        self.상태 = 새로운_상태
        self.save()

        if 새로운_상태 == 'OUT':
            SCM_models.SCM_제품.objects.create(
                stock_fk=self,
                상태='IN',
                수량=self.수량,
                처리자=self.처리자
            )

    # def get_status_history(self):
    #     """상태 변경 이력 조회"""
    #     return self.histories.all().order_by('changed_at')

    # def get_quantity_changes(self):
    #     """수량 변경 이력 조회"""
    #     return self.histories.filter(
    #         previous_quantity__ne=models.F('new_quantity')
    #     ).order_by('changed_at')

class StockHistory(models.Model):
    """재고 이력 관리 모델"""
    stock_fk = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name='histories', null=True, blank=True)
    이전상태 = models.CharField(max_length=10, choices=Stock.STATUS_CHOICES, null=True, blank=True)
    변경상태 = models.CharField(max_length=10, choices=Stock.STATUS_CHOICES, verbose_name='변경 상태' , null=True, blank=True)
    이전수량 = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], null=True, blank=True)
    변경수량 = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], null=True, blank=True)
    변경시간 = models.DateTimeField(auto_now_add=True, verbose_name='변경일시')
    처리자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True )
    비고 = models.TextField(blank=True, null=True, verbose_name='변경사유')

   
    class Meta:
        verbose_name = '재고 이력'
        verbose_name_plural = '재고 이력 목록'
        ordering = ['-변경시간']
        indexes = [
            models.Index(fields=['stock_fk', '변경시간']),
            models.Index(fields=['변경상태', '변경시간']),
        ]
    
    @transaction.atomic
    def 입고대기_생성(self, _obj: Stock):
        """재고 이력 생성"""
        self.stock_fk = _obj
        self.변경상태 = _obj.상태
        self.변경시간 = _obj.처리시간
        self.변경수량 = _obj.수량
        self.처리자 = _obj.처리자
        self.비고 = _obj.비고
        self.save()
