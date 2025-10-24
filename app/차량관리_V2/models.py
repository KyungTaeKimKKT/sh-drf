from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Sum , functions, Q, QuerySet

from datetime import date, datetime, timedelta

from users.models import User, Api_App권한

class 차량관리_기준정보(models.Model):
    법인명 = models.CharField(max_length=50, blank=True, null=True, default='')
    차종 = models.CharField(max_length=200, blank=True, null=True, default='')
    차량번호 = models.CharField(max_length=15, blank=True, null=True, default='', unique=True)
    타이어규격 = models.CharField(max_length=200, blank=True, null=True, default='')
    공급업체 = models.CharField(max_length=50, blank=True, null=True, default='')
    차량가격 = models.IntegerField( blank=True, null=True, default=0 )
    보증금   = models.IntegerField( blank=True, null=True, default=0 )
    대여료_VAT포함  = models.IntegerField( blank=True, null=True, default=0 )
    약정운행거리  = models.IntegerField( blank=True, null=True, default=0 , help_text="단위 km입니다.")
    초과거리부담금  = models.FloatField( blank=True, null=True, default=0 , help_text="단위 원/km입니다.")
    시작일 = models.DateField( default=timezone.now().date() )
    종료일 = models.DateField( default=timezone.now().date() )
    
    is_exist= models.BooleanField(default=True)

class 차량관리_사용자(models.Model):
    차량관리_기준정보_fk = models.ForeignKey('차량관리_기준정보', on_delete=models.CASCADE, null=True, blank=True , related_name='차량관리_V2_기준정보_fk')
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True , related_name='차량관리_V2_사용자_fk')


class 차량관리_운행DB(models.Model):
    차량번호_fk = models.ForeignKey(차량관리_기준정보, on_delete=models.DO_NOTHING, db_column='차량번호_fk' , help_text='차량번호 foreign-key입니다')
    일자 = models.DateTimeField( default=datetime.now() )
    주행거리 = models.IntegerField( default=0 , null=True, blank=True, help_text= "정비일 기준 주행거리(km)입니다" )
    정비금액 = models.IntegerField(  default=0 , null=True, blank=True, help_text= "정비금액입니다." )
    정비사항 = models.TextField ( default='', null=True, blank=True )
    비고 = models.TextField ( blank=True, null=True, default='')
    관련근거 = models.CharField(max_length=30, default='', null=True, blank=True )
    담당자_snapshot  = models.CharField (max_length=15, blank=True, null=True, default='' , help_text='이력을 위해 정적 필드 영역입니다.')
    담당자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, default='', on_delete=models.CASCADE, db_column='담당자_fk' , related_name='차량관리_V2_운행DB_담당자_fk')

class 차량관리_selector_DB(models.Model):
    구분 = models.CharField(max_length=15, blank=True, null=True, default='', help_text='selector DB에 구분요소로, 예로 법인, 공급업체 입니다.')
    DB_저장_id =  models.CharField(max_length=15, blank=True, null=True, default='', help_text='DB에 저장될 id로, 예로 상기 법인이 법인이면, (주)신우하이테크, (주)신우폴리텍스 입니다.')
    selector_표시명=  models.CharField(max_length=15, blank=True, null=True, default='', help_text='상기 id에 맞는 사용자에게 보여주는 이름입니다.')
