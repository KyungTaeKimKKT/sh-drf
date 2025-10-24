from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date
from elevator_info.models import Elevator_Summary_WO설치일

import uuid
from websocket import create_connection
import json



def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    return ( '인사평가/' + str(instance.평가기간_시작) +'-'+str(instance.평가기간_종료) +'/'+ filename) 


class 평가설정DB_Old(models.Model):
    
    id = models.AutoField ( primary_key=True )
    평가제목 = models.CharField(max_length=30, blank=True, null=True)
    평가기간_시작 = models.DateField ( default=date.today)
    평가기간_종료 = models.DateField ( default=date.today)
    
    평가점유_역량 = models.FloatField ( default = 0.0)
    평가점유_성과 = models.FloatField ( default = 0.0)
    평가점유_특별 = models.FloatField ( default = 0.0)
    
    평가점유_1차 = models.FloatField ( default = 0.0)
    평가점유_2차 = models.FloatField ( default = 0.0)
    평가점유_3차 = models.FloatField ( default = 0.0)
    
    등록자 = models.CharField(max_length=15, blank=True, null=True,default='') 
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )
    
    역량평가_file = models.FileField(upload_to=user_directory_path, max_length=254, default='', help_text="xlsx file format 필수 : ")
    평가체제_file = models.FileField(upload_to=user_directory_path, max_length=254, default='', help_text="xlsx file format 필수 : ")
    특별평가_file = models.FileField(upload_to=user_directory_path, max_length=254, default='', help_text="xlsx file format 필수 : ")
    
    is_시작 = models.BooleanField(default=False)
    is_종료 = models.BooleanField(default=False)  
    
    is_본인평가_세부할당 = models.BooleanField(default=False)
    is_1차평가_세부할당 = models.BooleanField(default=False)
    
    공지사항 = models.TextField( default='공지사항입니다. 필수사항입니다.', help_text="필수사항입니다")
    
    class Meta:
        managed = False
        db_table = '인사평가_v2_평가설정db'


class 종합평가_결과_Old(models.Model):
    id = models.AutoField ( primary_key=True )    
    평가제목_fk = models.ForeignKey(평가설정DB_Old, on_delete=models.CASCADE, db_column='평가제목_fk', blank=True, null=True)
    소속 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="...") 
    성명 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="...") 
    
    종합_본인 = models.FloatField ( default = 0.0)
    역량_본인 = models.FloatField ( default = 0.0)
    성과_본인 = models.FloatField ( default = 0.0)
    특별_본인 = models.FloatField ( default = 0.0)
    본인_is제출 = models.BooleanField(default=False)
    
    종합_1차 = models.FloatField ( default = 0.0)
    역량_1차 = models.FloatField ( default = 0.0)
    성과_1차 = models.FloatField ( default = 0.0)
    특별_1차 = models.FloatField ( default = 0.0)
    평가자_1차 = models.CharField(max_length=15, blank=True, null=True,default='') 
    is_1차제출 = models.BooleanField(default=False)
    is_1차완료 = models.BooleanField(default=False)
    
    종합_2차 = models.FloatField ( default = 0.0)
    역량_2차 = models.FloatField ( default = 0.0)
    성과_2차 = models.FloatField ( default = 0.0)
    특별_2차 = models.FloatField ( default = 0.0)
    평가자_2차 = models.CharField(max_length=15, blank=True, null=True,default='') 
    is_2차제출 = models.BooleanField(default=False)
    
    종합_3차 = models.FloatField ( default = 0.0)
    역량_3차 = models.FloatField ( default = 0.0)
    성과_3차 = models.FloatField ( default = 0.0)
    특별_3차 = models.FloatField ( default = 0.0)
    평가자_3차 = models.CharField(max_length=15, blank=True, null=True,default='') 
    is_3차제출 = models.BooleanField(default=False)
    
    종합_최종 = models.FloatField ( default = 0.0)
    역량_최종 = models.FloatField ( default = 0.0)
    성과_최종 = models.FloatField ( default = 0.0)
    특별_최종 = models.FloatField ( default = 0.0)
    
    최종_is정상 = models.BooleanField(default=False)
    is_초기세팅 = models.BooleanField(default=False)
    
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    class Meta:
        managed = False
        db_table = '인사평가_v2_종합평가_결과'