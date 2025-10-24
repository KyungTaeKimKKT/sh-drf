from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일


def 작업지침_directory_path(instance, filename):
    now = datetime.now()
    return ( '작업지침/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def 의장도_directory_path(instance, filename):
    now = datetime.now()
    return ( '작업지침/의장도/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def rendering_directory_path(instance, filename):
    now = datetime.now()
    return ( '작업지침/rendering/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class 결재내용(models.Model):
    결재자 = models.ForeignKey( settings.AUTH_USER_MODEL,  on_delete=models.CASCADE,)
    결재결과 = models.BooleanField( null=True, blank=True )
    결재의견 = models.TextField(blank=True, null=True)
    결재일 = models.DateTimeField( blank=True, null=True )
    의뢰일 = models.DateTimeField( blank=True, null=True)

    def save(self, *args, **kwargs):
        self.결재일 = timezone.now()
        super(결재내용, self).save(*args, **kwargs) 
        return self


class 첨부file(models.Model):
    file = models.FileField(upload_to=작업지침_directory_path, max_length=254, null=True, blank=True)

class 의장도( models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    file = models.FileField(upload_to=의장도_directory_path, max_length=254, null=True, blank=True)
    순서 = models.IntegerField(default=0)

class Rendering_file(models.Model):
    file = models.FileField(upload_to=rendering_directory_path, max_length=254, null=True, blank=True)

class Process(models.Model):

    적용부품 = models.CharField(max_length=30,  null=True, blank=True)
    적용패널 = models.CharField(max_length=50,  null=True, blank=True)
    Material = models.CharField(max_length=30,  null=True, blank=True)
    대표Process = RichTextField(null=True, blank=True)
    상세Process = RichTextField(null=True, blank=True)
    # ProcessColor = models.CharField(max_length=20,  null=True, blank=True)
    비고 = models.TextField(blank=True, null=True) 
    대표Process_Text = models.TextField(null=True, blank=True)
    상세Process_Text = models.TextField(null=True, blank=True)
    표시순서 = models.IntegerField(default=0)


class 작업지침(models.Model):
    process_fks = models.ManyToManyField( Process ,null=True, blank=True , related_name='Process+')   
    첨부file_fks = models.ManyToManyField( 첨부file ,null=True, blank=True , related_name='첨부file+')    
    결재내용_fks = models.ManyToManyField ( 결재내용, null=True, blank=True , related_name='결재선+')
    el_info_fk = models.ForeignKey (Elevator_Summary_WO설치일, on_delete=models.CASCADE, null=True, blank=True , related_name='el_info+')
    의장도_fks = models.ManyToManyField ( 의장도 ,null=True, blank=True , related_name='의장도+' )  

    제목 = RichTextField(null=True, blank=True)
    구분 = models.CharField(max_length=20,  null=True, blank=True)
    Proj_No = models.CharField(max_length=30,  null=True, blank=True)
    
    is_배포 = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)

    수량 = models.IntegerField (blank=True, null=True)
    납기일 = models.DateField(  blank=True, null=True)
    작성일 = models.DateField(  blank=True, null=True)
    고객사 = models.CharField(max_length=50,  null=True, blank=True)
    작성자_fk =  models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,  null=True, blank=True, related_name='_작성자_fk')
    담당 = models.CharField(max_length=50,  null=True, blank=True)
    진행현황 = models.CharField(max_length=20,  null=True, blank=True)
    영업담당자_fk =  models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,  null=True, blank=True, related_name='_영업담당자_fk')
    # 영업담당 = models.CharField(max_length=20,  null=True, blank=True)

    Rendering = models.ForeignKey( Rendering_file, on_delete=models.DO_NOTHING, null=True, blank=True)

    고객요청사항 = models.CharField(max_length=250,  null=True, blank=True)
    고객성향 = models.CharField(max_length=250,  null=True, blank=True)
    특이사항 = models.CharField(max_length=250,  null=True, blank=True)
    집중점검항목 = models.CharField(max_length=250,  null=True, blank=True)
    검사요청사항 = models.CharField(max_length=250,  null=True, blank=True)   

    #ECO 관련 추가됨
    변경사유_내용 = models.TextField(null=True, blank=True)
    Rev = models.IntegerField(default=1)
    prev_작지 = models.ForeignKey( 'self', on_delete=models.CASCADE, null=True, blank=True )

    ### django-simple-history
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # is_배포가 True로 변경될 때 로직 처리
        self.is_valid = self.is_배포
        if self.is_배포:            
            # 이전 버전이 있다면 is_valid를 False로 설정
            if self.prev_작지:
                작업지침.objects.filter(pk=self.prev_작지.pk).update(is_valid=False)
        
        super().save(*args, **kwargs)

    
    def _get_진행현황(self):        
        if ( not self.결재내용_fks.count() ): return '작성중'
        
        for 결재instance in self.결재내용_fks.all() :
            if ( 결재instance.결재의견 is not None ) :
                if( not 결재instance.결재의견 ): return '반려'

        for 결재instance in self.결재내용_fks.all() :
            if ( 결재instance.결재의견 is None) : return '진행중'

        return '완료'        


    
class Group작업지침 ( models.Model):
    group = models.ManyToManyField( 작업지침, blank=True , related_name='group+')    
