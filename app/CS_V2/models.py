from django.db import models
from django.conf import settings

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from datetime import datetime, date

def 고객요청_directory_path(instance, filename):
    now = datetime.now()
    return ( '품질경영/고객요청/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 


class CS_Claim (models.Model):
    진행현황_선택 = [
        ('작성', '작성'),
        ('의뢰', '의뢰'),
        ('접수', '접수'),
        ('완료', '완료'),
        ('반려', '반려'),
    ]

    el_info_fk = models.ForeignKey(Elevator_Summary_WO설치일, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
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
    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    등록일 = models.DateTimeField(null=True, blank=True)
    완료자 = models.CharField(max_length=50,  null=True, blank=True)
    완료자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='+' )
    완료일 = models.DateTimeField(null=True, blank=True)

    완료요청일 = models.DateField(null=True, blank=True)

    ### ✅ 25-7-23 추가 : 접수 process 추가
    접수일 = models.DateTimeField(null=True, blank=True)
    완료목표일 = models.DateField(null=True, blank=True)
    접수자 = models.CharField(max_length=50,  null=True, blank=True)
    접수자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='+' )
    진행계획 = models.TextField(null=True, blank=True)
    반려사유 = models.TextField(null=True, blank=True)


class CS_Activity(models.Model):
    claim_fk = models.ForeignKey( CS_Claim, on_delete=models.CASCADE, null=True, blank=True , related_name='CS_Activity_set')
    활동현황 = models.TextField(null=True, blank=True)
    활동일 = models.DateTimeField(null=True, blank=True)
    등록자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    등록일 = models.DateTimeField(null=True, blank=True)


class CS_Claim_File(models.Model):
    claim_fk = models.ForeignKey( CS_Claim, on_delete=models.CASCADE, null=True, blank=True, related_name='CS_Claim_File_set')
    file = models.FileField(upload_to=고객요청_directory_path, max_length=254, null=True, blank=True)


class CS_Activity_File(models.Model):
    activity_fk = models.ForeignKey( CS_Activity, on_delete=models.CASCADE, null=True, blank=True, related_name='CS_Activity_File_set')
    file = models.FileField(upload_to=고객요청_directory_path, max_length=254, null=True, blank=True)

