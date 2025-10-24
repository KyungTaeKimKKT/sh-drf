from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User # custom User model import
from 작업지침.models import 작업지침
from datetime import datetime, date

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일


### replace 할 것 : /, . ()
def upload_to_영업수주_일정(instance, filename):
    return f'영업수주/일정/{instance.기준년월}/{filename}'

def upload_to_영업수주_금액(instance, filename):
    return f'영업수주/금액/{instance.기준년월}/{filename}'

class 영업수주_관리(models.Model):
    기준년월 = models.CharField(max_length=7, blank=True, null=True)  # YYYY-MM 형식
    일정file = models.FileField(upload_to=upload_to_영업수주_일정, blank=True, null=True)
    금액file = models.FileField(upload_to=upload_to_영업수주_금액, blank=True, null=True)
    등록자_fk = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='영업수주_관리_등록자')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    비고 = models.TextField(blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)

class 자재내역_To_의장_Mapping(models.Model):
    자재내역 = models.CharField( max_length=250, blank=True, null=True)
    의장 = models.CharField( max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    기준 = models.CharField ( max_length=10, blank=True, null=True)

class 영업수주_금액(models.Model):
    관리_fk = models.ForeignKey('영업수주.영업수주_관리', on_delete=models.CASCADE, related_name='영업수주_금액_관리_set', null=True, blank=True)

    일정_fk = models.ForeignKey('영업수주.영업수주_일정', on_delete=models.CASCADE, related_name='영업수주_금액_일정_set', null=True, blank=True)
    의장_fk = models.ForeignKey('영업수주.자재내역_To_의장_Mapping', on_delete=models.CASCADE, related_name='영업수주_금액_자재내역_To_의장_Mapping_set', null=True, blank=True)
    발주번호 =  models.CharField( max_length=20, blank=True, null=True)
    # 항번 =  models.IntegerField(default=0)
    # 처리상태 =  models.CharField( max_length=250, blank=True, null=True)
    # 구매그룹 =  models.CharField( max_length=250, blank=True, null=True)
    # 발주유형 =  models.CharField( max_length=250, blank=True, null=True)
    # 납기준수여부 =  models.CharField( max_length=250, blank=True, null=True)
    # 납기미준수사유 =  models.CharField( max_length=250, blank=True, null=True)
    # 납품예정일 =  models.DateField( blank=True, null=True)
    # 최초입력일자 =  models.DateField( blank=True, null=True)
    # 변경일자 =  models.DateField( blank=True, null=True)
    # Plant명 =  models.CharField( max_length=250, blank=True, null=True)
    # 저장위치 =  models.CharField( max_length=250, blank=True, null=True)
    Proj_번호 =  models.CharField( max_length=250, blank=True, null=True, db_index=True)
    공사_현장명 =  models.CharField( max_length=250, blank=True, null=True)
    # 입고예정일 =  models.DateField( blank=True, null=True)
    자재번호 =  models.CharField( max_length=250, blank=True, null=True)
    # 구자재번호 =  models.CharField( max_length=250, blank=True, null=True)
    자재내역 =  models.CharField( max_length=250, blank=True, null=True)
    # 생산오더번호 =  models.IntegerField(default=0)
    # 자재담당자 =  models.CharField( max_length=250, blank=True, null=True)
    # BOX번호 =  models.CharField( max_length=250, blank=True, null=True)
    # BOX품명 =  models.CharField( max_length=250, blank=True, null=True)
    # BOX구분 =  models.CharField( max_length=250, blank=True, null=True)
    호기번호_WBS =  models.CharField( max_length=250, blank=True, null=True)
    호기번호 = models.CharField( max_length=250, blank=True, null=True, db_index=True)
    단위 =  models.CharField( max_length=250, blank=True, null=True)
    # 통화 =  models.CharField( max_length=250, blank=True, null=True)
    발주단가 =  models.IntegerField(default=0)
    발주수량 =  models.IntegerField(default=0)
    금액 =  models.IntegerField(default=0)
    # 불량수량 =  models.IntegerField(default=0)
    발주잔량 =  models.IntegerField(default=0)
    신우_단가 =  models.IntegerField(default=0)
    신우_실제금액 =  models.IntegerField(default=0)
    # 치수 =  models.IntegerField(default=0)
    도면번호 =  models.CharField( max_length=250, blank=True, null=True)
    # 품목범주 =  models.IntegerField(default=0)
    현장대수 =  models.IntegerField(default=0)
    # 계정범주 =  models.CharField( max_length=250, blank=True, null=True)
    # 내_외자구분 =  models.CharField( max_length=250, blank=True, null=True)
    변경납기일 =  models.DateField( blank=True, null=True)
    최초납기일 =  models.DateField( blank=True, null=True)
    # 납기일변경일시 =  models.DateTimeField( blank=True, null=True)
    생산계획일 =  models.DateTimeField( blank=True, null=True)
    # 생산계획변경일 =  models.DateTimeField( blank=True, null=True)
    # 애칭번호 =  models.IntegerField(default=0)
    # 자재별특성치 =  models.CharField( max_length=250, blank=True, null=True)
    # 특성치변경일시 =  models.DateTimeField( blank=True, null=True)
    # 발주승인일시 =  models.DateTimeField( blank=True, null=True)
    # 승인담당자 =  models.CharField( max_length=250, blank=True, null=True)
    # 발주삭제일시 =  models.DateTimeField( blank=True, null=True)
    # 삭제담당자 =  models.CharField( max_length=250, blank=True, null=True)
    # JAMB_실측일 =  models.DateField( blank=True, null=True)
    # 마감내역 =  models.CharField( max_length=250, blank=True, null=True)
    설치협력사 =  models.CharField( max_length=250, blank=True, null=True)
    # 보수청구협력사 =  models.IntegerField(default=0)
    # 유관협력사 =  models.IntegerField(default=0)
    출하일자 =  models.DateField( blank=True, null=True)
    공사주석 =  models.TextField( blank=True, null=True)
    # PJT상태 =  models.CharField( max_length=250, blank=True, null=True)
    # 비고 =  models.CharField( max_length=250, blank=True, null=True)
    거래명세서번호 =  models.CharField( max_length=250, blank=True, null=True)
    # 거래명세서상태 =  models.CharField( max_length=250, blank=True, null=True)
    # HS_Code =  models.IntegerField(default=0)
    # HS_Code명 =  models.IntegerField(default=0)
    # 인코텀즈 =  models.IntegerField(default=0)
    # 지급조건 =  models.CharField( max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

class 영업수주_일정(models.Model):
    관리_fk = models.ForeignKey('영업수주.영업수주_관리', on_delete=models.CASCADE, related_name='영업수주_일정_관리_set', null=True, blank=True)

    GATE =  models.CharField( max_length=250, blank=True, null=True)
    상태 =  models.CharField( max_length=250, blank=True, null=True)
    프로젝트 =  models.CharField( max_length=250, blank=True, null=True)
    호기번호 =  models.CharField( max_length=250, blank=True, null=True)
    현장호기 =  models.CharField( max_length=250, blank=True, null=True)
    프로젝트명 =  models.CharField( max_length=250, blank=True, null=True)
    기종 =  models.CharField( max_length=250, blank=True, null=True)
    사양 =  models.CharField( max_length=250, blank=True, null=True)
    기계실_출하요청일 =  models.DateField( blank=True, null=True)
    구조물_출하요청일 =  models.DateField( blank=True, null=True)
    출입구_출하요청일 =  models.DateField(  blank=True, null=True)
    DOOR_출하요청일 =  models.DateField(  blank=True, null=True)
    CAGE_출하요청일 =  models.DateField(  blank=True, null=True)
    바닥재_출하요청일 =  models.DateField(  blank=True, null=True)
    착공F =  models.CharField( max_length=250, blank=True, null=True)
    착공일 =  models.DateField(  blank=True, null=True)
    설치투입일 = models.DateField(  blank=True, null=True)
    준공예정일 = models.DateField(  blank=True, null=True)
    준공F = models.CharField( max_length=250, blank=True, null=True)
    준공일 = models.DateField(null=True, blank=True)
    지사 = models.CharField( max_length=250, blank=True, null=True)
    설치PM = models.CharField( max_length=250, blank=True, null=True)
    협력업체 = models.CharField( max_length=250, blank=True, null=True)
    작업팀장 = models.CharField( max_length=250, blank=True, null=True)
    양중업체 = models.CharField( max_length=250, blank=True, null=True)
    양중팀장 = models.CharField( max_length=250, blank=True, null=True)
    상태_1 = models.CharField( max_length=250, blank=True, null=True)