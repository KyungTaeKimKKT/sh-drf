from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User # custom User model import
from 작업지침.models import 작업지침
from datetime import datetime, date

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일


def 부적합_directory_path(instance, filename):
    now = datetime.now()
    return ( '품질경영/부적합/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class 부적합_file( models.Model):
    file = models.FileField(upload_to=부적합_directory_path, max_length=254, null=True, blank=True)


class 부적합내용(models.Model):
    품목 = models.CharField(max_length=250, null=True, blank=True)
    부적합수량 = models.CharField(max_length=250, null=True, blank=True)
    원인 = models.CharField(max_length=250,  null=True, blank=True)
    귀책부서 = models.CharField( max_length=250, blank=True, null=True)
    조치방안 = models.CharField(max_length=250,  null=True, blank=True)
    조치일정 = models.CharField(max_length=250,  null=True, blank=True)
    표시순서 = models.IntegerField(default=0)
    

class NCR(models.Model):
    file_fks =  models.ManyToManyField( 부적합_file )
    첨부파일수 = models.IntegerField(default=0 )
    제목 = models.CharField(max_length=100, null=True, blank=True)
    귀책공정 = models.CharField(max_length=100, null=True, blank=True)
    발행번호 = models.CharField(max_length=20,  null=True, blank=True)
    발생일자 = models.DateField(  blank=True, null=True)
    발견자 = models.CharField(max_length=20,  null=True, blank=True)
    고객사 = models.CharField(max_length=20,  null=True, blank=True)
    작성일자 = models.DateField(  blank=True, null=True)
    작성자_fk = models.ForeignKey( User, on_delete=models.CASCADE, null=True, blank=True)
    현장명 = models.CharField(max_length=50,  null=True, blank=True)
    소재 = models.CharField(max_length=20,  null=True, blank=True)
    의장명 = models.CharField(max_length=250,  null=True, blank=True)
    OP = models.CharField(max_length=20,  null=True, blank=True)
    자재명 = models.CharField(max_length=20,  null=True, blank=True)
    수량 = models.IntegerField(default=0)
    단위 = models.CharField(max_length=20,  null=True, blank=True)
    contents_fks = models.ManyToManyField( 부적합내용 )
    부적합상세 = models.TextField( null=True, blank=True )
    임시조치방안 = models.TextField( null=True, blank=True )
    일정사항 = models.TextField( null=True, blank=True )
    is_배포 = models.BooleanField(default=False)
    # 품질비용_fk

    ### Pyqt5 에서 groupbox radio button 으로 구현
    분류 = models.CharField(max_length=10,  null=True, blank=True)
    구분 = models.CharField(max_length=10,  null=True, blank=True)
    조치사항 = models.CharField(max_length=10,  null=True, blank=True)

    작지_fk = models.ForeignKey ( 작업지침, on_delete=models.CASCADE, null=True, blank=True)


class 품질비용(models.Model):
    NCR_fk = models.ForeignKey ( NCR, on_delete=models.CASCADE, null=True, blank=True)
    소재비 = models.IntegerField(default=0)
    의장비 = models.IntegerField(default=0)
    판금비 = models.IntegerField(default=0)
    설치비 = models.IntegerField(default=0)
    운송비 = models.IntegerField(default=0)
    코팅비 = models.IntegerField(default=0)
    합계 = models.IntegerField(default=0)

    # def save(self, *args, **kwargs):
    #     fields = [f.name for f in self._meta.fields] 
    #     제외fields = ['NCR_fk', '합계']

    #     for field in [elm for elm in fields  if elm not in 제외fields] :
    #         if ( value := getattr(self, field ) ) :
    #             self.합계 += value
    #     # self.진행현황 = self._get_진행현황()
        
    #     super().save(*args, **kwargs) 
    #     return self

    # 작업명 = models.CharField(max_length=100,  null=True, blank=True)
    # 계획수량 = models.IntegerField(null=True, blank=True)
    # 생산계획일 =  models.DateField(  blank=True, null=True)
    # 확정납기일 = models.DateField(  blank=True, null=True)
    
    # 계획수립시간 = models.DateTimeField(null=True)

def 처리현황_directory_path(instance, filename):
    now = datetime.now()
    return ( '품질경영/처리현황/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class Action_File( models.Model):
    file = models.FileField(upload_to=처리현황_directory_path, max_length=254, null=True, blank=True)

def 고객요청_directory_path(instance, filename):
    now = datetime.now()
    return ( '품질경영/고객요청/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class Claim_File( models.Model):
    file = models.FileField(upload_to=고객요청_directory_path, max_length=254, null=True, blank=True)


class Action(models.Model):
    action_files = models.ManyToManyField( Action_File )  
    활동현황 = models.TextField(null=True, blank=True)
    활동일 = models.DateTimeField(null=True, blank=True)
    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    등록일 = models.DateTimeField(null=True, blank=True)


class CS_Manage(models.Model):
    진행현황_선택 = [
        ('작성', '작성'),
        ('Open', 'Open'),
        ('Close', 'Close'),
    ]

    el_info_fk = models.ForeignKey(Elevator_Summary_WO설치일, on_delete=models.CASCADE, null=True, blank=True )
    el수량 = models.IntegerField(default=0)
    운행층수 = models.IntegerField(default=0)
    action_fks = models.ManyToManyField( Action , blank=True) 
    claim_file_fks = models.ManyToManyField( Claim_File  , blank=True)  
    

    현장명 = models.CharField(max_length=200,  null=True, blank=True)
    현장주소 = models.CharField(max_length=200,  null=True, blank=True)
    Elevator사 = models.CharField(max_length=50,  null=True, blank=True)

    불만요청사항 = models.TextField(null=True, blank=True)
    고객명 = models.CharField(max_length=50,  null=True, blank=True)
    고객연락처 = models.CharField(max_length=50,  null=True, blank=True)
    차수 = models.IntegerField(default=1)
    진행현황 = models.CharField (max_length=10,choices=진행현황_선택, default='작성',null=True, blank=True)

    품질비용 = models.IntegerField(default=0)

    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='등록자_fk')
    등록일 = models.DateTimeField(null=True, blank=True)
    
    완료일 = models.DateTimeField(null=True, blank=True)
    완료자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='완료자_fk' )



##### fk 로 modeling
class CS_Claim (models.Model):
    진행현황_선택 = [
        ('작성', '작성'),
        ('Open', 'Open'),
        ('Close', 'Close'),
    ]

    el_info_fk = models.ForeignKey(Elevator_Summary_WO설치일, on_delete=models.CASCADE, null=True, blank=True, related_name='CS_Claim_el_info_fk')
    el수량 = models.IntegerField(default=0)
    운행층수 = models.IntegerField(default=0)
    

    현장명 = models.CharField(max_length=200,  null=True, blank=True)
    현장주소 = models.CharField(max_length=200,  null=True, blank=True)
    Elevator사 = models.CharField(max_length=50,  null=True, blank=True)

    부적합유형 = models.CharField(max_length=50,  null=True, blank=True)
    불만요청사항 = models.TextField(null=True, blank=True)
    고객명 = models.CharField(max_length=50,  null=True, blank=True)
    고객연락처 = models.CharField(max_length=50,  null=True, blank=True)
    차수 = models.IntegerField(default=1)
    진행현황 = models.CharField (max_length=10,choices=진행현황_선택, default='작성',null=True, blank=True)

    품질비용 = models.IntegerField(default=0)
    등록자 = models.CharField(max_length=50,  null=True, blank=True)
    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cs_claim_등록자_set')
    등록일 = models.DateTimeField(null=True, blank=True)
    완료자 = models.CharField(max_length=50,  null=True, blank=True)
    완료자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cs_claim_완료자_set' )
    완료일 = models.DateTimeField(null=True, blank=True)

    완료요청일 = models.DateField(null=True, blank=True)

class CS_Activity(models.Model):
    claim_fk = models.ForeignKey( CS_Claim, on_delete=models.CASCADE, null=True, blank=True , related_name='cs_activity_set')
    활동현황 = models.TextField(null=True, blank=True)
    활동일 = models.DateTimeField(null=True, blank=True)
    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cs_activity_등록자_set')
    등록일 = models.DateTimeField(null=True, blank=True)
    예정_시작일 = models.DateField(null=True, blank=True)
    예정_완료일 = models.DateField(null=True, blank=True)

class CS_Claim_File(models.Model):
    claim_fk = models.ForeignKey( CS_Claim, on_delete=models.CASCADE, null=True, blank=True, related_name='cs_claim_file_set')
    file = models.FileField(upload_to=고객요청_directory_path, max_length=254, null=True, blank=True)


class CS_Activity_File(models.Model):
    activity_fk = models.ForeignKey( CS_Activity, on_delete=models.CASCADE, null=True, blank=True, related_name='cs_activity_file_set')
    file = models.FileField(upload_to=고객요청_directory_path, max_length=254, null=True, blank=True)

