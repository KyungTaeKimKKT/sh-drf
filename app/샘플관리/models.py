from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일


def 샘플의뢰_directory_path(instance, filename):
    now = datetime.now()
    return ( '샘플의뢰/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def 샘플완료_directory_path(instance, filename):
    now = datetime.now()
    return ( '샘플의뢰/완료파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 


class 첨부file(models.Model):
    file = models.FileField(upload_to=샘플의뢰_directory_path, max_length=254, null=True, blank=True)

class 완료file(models.Model):
    file = models.FileField(upload_to=샘플완료_directory_path, max_length=254, null=True, blank=True)

class Process(models.Model):
    Item = models.CharField(max_length=20,  null=True, blank=True)
    작업형태 = models.CharField(max_length=20,  null=True, blank=True)
    제작형태 = models.CharField(max_length=20,  null=True, blank=True)
    소재종류 = models.CharField(max_length=20,  null=True, blank=True)
    소재Size = models.CharField(max_length=20,  null=True, blank=True)
    수량 = models.IntegerField(null=True)
    단위 = models.CharField(max_length=20,  null=True, blank=True)
    대표Process = RichTextField(null=True, blank=True)
    상세Process = RichTextField(null=True, blank=True)
    패턴No = models.CharField(max_length=20,  null=True, blank=True)
    비고 = models.TextField(blank=True, null=True) 
    대표Process_Text = models.TextField(null=True, blank=True)
    상세Process_Text = models.TextField(null=True, blank=True)
    표시순서 = models.IntegerField(default =0)


class 샘플관리(models.Model):
    process_fks = models.ManyToManyField( Process ,null=True, blank=True , related_name='Process+')   
    첨부file_fks = models.ManyToManyField( 첨부file ,null=True, blank=True , related_name='첨부file+')    
    # 완료file_fks = models.ManyToManyField( 완료file ,null=True, blank=True , related_name='완료file+')  
    # 결재내용_fks = models.ManyToManyField ( 결재내용, null=True, blank=True , related_name='결재선+')

    고객사 = models.CharField(max_length=20,  null=True, blank=True)
    요청건명 = models.CharField(max_length=100,  null=True, blank=True)
    용도_현장명 = models.CharField(max_length=100,  null=True, blank=True)
    진행현황 = models.CharField(max_length=20, null=True, blank=True)
    납기일 = models.DateField(  blank=True, null=True)
    요청일 = models.DateField(  blank=True, null=True)
    
    요청자_fk = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='_요청자_fk')
    납품차수 = models.IntegerField(default=1)

    시편 = models.IntegerField(default=0)
    NCT = models.IntegerField(default=0)
    절곡 = models.IntegerField(default=0)
    조립 = models.IntegerField(default=0)
    설치 = models.IntegerField(default=0)

    불요 = models.BooleanField(default=True)
    Book = models.IntegerField(default=0)
    Board = models.IntegerField(default=0)

    비고 = models.TextField(default='')

    현장명 = models.CharField(max_length=30, null=True, blank=True)
    EL사 = models.CharField(max_length=30, null=True, blank=True)
    구분 = models.CharField(max_length=30, null=True, blank=True)
    생산적용시점 = models.DateField(  blank=True, null=True)
    # 수량 = models.IntegerField(default=0)

    is_의뢰 = models.BooleanField(default=False)
    작성일 = models.DateTimeField(  blank=True, null=True)

    ### 샘플 결과
    완료file_fks = models.ManyToManyField( 완료file ,null=True, blank=True , related_name='완료file+')    
    완료의견 = models.TextField(default='')
    is_완료 = models.BooleanField(default=False)
    완료일 = models.DateTimeField(null=True)
    완료자_fk = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='_완료자_fk')


# class 샘플결과(models.Model):
#     샘플의뢰_fk = models.ForeignKey(샘플의뢰,   on_delete=models.CASCADE, null=True, blank=True)
#     완료file_fks = models.ManyToManyField( 완료file ,null=True, blank=True , related_name='완료file+')    
#     완료의견 = models.TextField(default='')
#     is_완료 = models.BooleanField(default=False)
#     완료일 = models.DateTimeField(null=True)
#     등록자 = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    
# class Group작업지침 ( models.Model):
#     group = models.ManyToManyField( 샘플의뢰, blank=True , related_name='group+')    
