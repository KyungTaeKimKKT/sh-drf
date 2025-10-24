from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date
from elevator_info.models import Elevator_Summary_WO설치일


# ic.disable()

import uuid
from websocket import create_connection
import json


class 역량평가사전_DB(models.Model):
    구분 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="공통역량, 직무역량(공통), 리더십역량 등: 추가 가능") 
    항목 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="열정, 원칙준수 , .....") 
    정의 = models.CharField(max_length=255, blank=True, null=True,default='', help_text="......")
         
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='역량평가사전_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

class 평가설정_DB ( models.Model) :
    제목 = models.CharField(max_length=30, blank=True, null=True)
    시작 = models.DateField ( default=date.today)
    종료 = models.DateField ( default=date.today)
    
    총평가차수 = models.IntegerField( default=2)
    # 평가체계_fk = models.ForeignKey ( 평가체계_DB, on_delete=models.DO_NOTHING , related_name='_평가체계')

    점유_역량 = models.IntegerField ( default = 30)
    점유_성과 = models.IntegerField ( default = 50)
    점유_특별 = models.IntegerField ( default = 20)    

    차수별_점유 = models.JSONField(default=lambda: {'0': 0, '1':50, '2':50})
    차수별_유형 = models.JSONField(default=lambda: {'0':'개별', '1':'개별', '2':'종합'})
    
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='평가설정_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    is_시작 = models.BooleanField(default=False)
    is_종료 = models.BooleanField(default=False) 

def get_active_평가설정():
    return 평가설정_DB.objects.filter( is_시작=True, is_종료=False ).latest('id')

class 평가체계_DB ( models.Model ):
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, related_name='평가체계_평가설정')
    평가자 =   models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='평가체계_평가자')
    피평가자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='평가체계_피평가자')
    차수 =  models.IntegerField( default=0)
    is_참여 = models.BooleanField( default=True )
    is_submit = models.BooleanField( default=False )
    

class 역량평가_항목_DB_V2(models.Model):
    평가설정_fk = models.ForeignKey('평가설정_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_항목_평가설정_fk')
    항목 = models.ForeignKey('역량평가사전_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_항목_항목')
    차수 = models.IntegerField(default=0)
    

class 역량평가_DB_V2(models.Model):
    평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_평가체계_fk')
    is_submit = models.BooleanField(default=False )
    평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
    평가점수 = models.FloatField(default=0)
    
    

class 세부_역량평가_DB_V2(models.Model):
    역량평가_fk = models.ForeignKey('역량평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_역량평가_fk')
    항목 = models.ForeignKey('역량평가_항목_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_역량평가_항목')
    평가점수 = models.FloatField(default=0)    
    
    
class 성과평가_DB_V2(models.Model):
    평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='성과평가_평가체계_fk')
    is_submit = models.BooleanField(default=False )
    평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
    평가점수 = models.FloatField(default=0)
    

class 세부_성과평가_DB_V2(models.Model):
    성과평가_fk = models.ForeignKey('성과평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_성과평가_fk')
    
    과제명 = models.CharField ( max_length=250, blank=True, null=True )
    과제목표 = models.TextField( blank=True, null=True,default='', help_text=".....") 
    성과  = models.TextField( blank=True, null=True,default='', help_text=".....") 
    목표달성률 = models.CharField(max_length=250, blank=True, null=True,default='', help_text=".....")
    실행기간   = models.CharField(max_length=50, blank=True, null=True,default='', help_text=".....")
    가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
    평가점수 = models.FloatField ( default = 0.0)
         
 
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )
    
class 특별평가_DB_V2(models.Model):
    평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='특별평가_평가체계_fk')
    is_submit = models.BooleanField(default=False )
    평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
    평가점수 = models.FloatField(default=0)
    
class 세부_특별평가_DB_V2(models.Model):
    특별평가_fk = models.ForeignKey('특별평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_특별평가_fk')

    구분 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="품질, 혁신 등") 
    성과 = models.TextField(blank=True, null=True, default='', help_text="항목 예시 ") 
    가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
    평가점수 = models.FloatField ( default = 0.0)
         
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )