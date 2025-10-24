from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta


class 무재해_DB(models.Model): 
    무재해시작 = models.DateTimeField ( default='')
    
    is_active =  models.BooleanField( default=True)
    published_date = models.DateTimeField ( default='')
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str( self.무재해시작 ) #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 생산계획_사용자_DB(models.Model): 
    사용자 = models.CharField(max_length=10, default='', help_text='사용자 성명을 기입, 예)이준환')
    사용구분 = models.CharField(max_length=10, default='', help_text='HI, PO, 판금 으로 기입')
    사용List = models.CharField(max_length=150, default='', help_text='S-01,S-02,...로 입력, 공란은 없이 ,로 구분')
 
    등록일 = models.DateTimeField ( default=timezone.now )

    
class 휴식시간_DB (models.Model): 
    휴식시간_시작 = models.TimeField(default="10:30:00", help_text="휴식시간 시작 시간 입력")
    휴식시간_종료 = models.TimeField(default="10:40:00", help_text="휴식시간 종료 시간 입력")
    적용대상 = models.CharField(max_length=50, default='', help_text='S-01,S-02,...로 입력, 공란은 없이 ,로 구분')
    # 휴식명 = models.CharField(max_length=20, default='', help_text='휴식명 기입')
    
    등록일 = models.DateTimeField ( default=timezone.now )
    
class SENSOR_NETWORK_DB (models.Model): 
    sensor_id = models.CharField(max_length=10, blank=True, null=True, default='')
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField (default=True )
    
    등록일 = models.DateTimeField ( default=timezone.now )
