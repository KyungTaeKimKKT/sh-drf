from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField
from simple_history.models import HistoricalRecords

from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date
import copy

import uuid
from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
import 작업지침.models as 작지
import 품질경영.models as 품질경영

def JAMB_directory_path(instance, filename):
	now = datetime.now()
	return ( '생산지시/JAMB/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 


def 생산지시_directory_path(instance, filename):
	now = datetime.now()
	return ( '생산지시/도면파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def spg생산지시_directory_path(instance, filename):
	now = datetime.now()
	return ( '생산지시/spg생산지시/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def tab_made_directory_path(instance, filename):
	now = datetime.now()
	return ( '생산지시/tab_made생산지시/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class JAMB_file(models.Model):
	file = models.FileField(upload_to=JAMB_directory_path, max_length=254, null=True, blank=True)

class TAB_Made_file(models.Model):
	title = models.CharField(max_length=30,  null=True, blank=True)
	file = models.FileField(upload_to=tab_made_directory_path, max_length=254, null=True, blank=True)

class SPG_file(models.Model):
	file = models.FileField(upload_to=spg생산지시_directory_path, max_length=254, null=True, blank=True)

class 도면file(models.Model):
	file = models.FileField(upload_to=생산지시_directory_path, max_length=254, null=True, blank=True)

class JAMB_발주정보(models.Model):
	JAMB_files_fks = models.ManyToManyField( JAMB_file, related_name='JAMB_files_fks+')
	발주사 = models.CharField(max_length=30,  null=True, blank=True)
	발주담당자 = models.CharField(max_length=20,  null=True, blank=True)
	발주일 = models.DateField(  blank=True, null=True)
	출하요청일 = models.DateField(  blank=True, null=True)
	등록일 = models.DateField(default=date.today() )
	확정 = models.BooleanField ( blank=True, null=True )

class 도면상세내용 ( models.Model):
	""" 사용안함"""
	품목 = models.CharField(max_length=30,  null=True, blank=True)
	도면 = models.CharField(max_length=30,  null=True, blank=True)
	소재 = models.CharField(max_length=30,  null=True, blank=True)
	치수 = models.IntegerField (  blank=True, null=True)
	총수량 = models.IntegerField (  blank=True, null=True)
	개별수량 = models.FloatField (  blank=True, null=True)


class 도면정보(models.Model):
	# 상세내용_fks = models.ManyToManyField( 도면상세내용, related_name='도면상세내용+') 
	고객사 = models.CharField(max_length=30, blank=True, null=True)
	공사번호 = models.CharField(max_length=30,  null=True, blank=True)
	납기일_Door = models.DateField(  blank=True, null=True)
	납기일_Cage = models.DateField(  blank=True, null=True)
	발주일 = models.DateField(  blank=True, null=True)
	사양 = models.CharField(max_length=30,  null=True, blank=True)
	인승 = models.CharField(max_length=30, blank=True, null=True)

	호기 = models.CharField(max_length=30,  null=True, blank=True)
	현장명 =  models.CharField(max_length=30,  null=True, blank=True)
	JJ = models.IntegerField ( default= 0 )
	CH = models.IntegerField ( default= 0 )
	HH = models.IntegerField ( default= 0 )
	
	HD_기타층_수량1 =  models.IntegerField ( default= 0 )
	HD_기타층_수량2 =  models.IntegerField ( default= 0 )
	HD_기준층_수량1 =  models.IntegerField ( default= 0 )
	HD_기준층_수량2 =  models.IntegerField ( default= 0 )    
	CD_수량1 = models.IntegerField ( default= 0 )
	CD_수량2 = models.IntegerField ( default= 0 )
	CW_수량1 = models.IntegerField ( default= 0 )
	CW_수량2 = models.FloatField ( default= 0 )
	상판_수량1 = models.IntegerField ( default= 0 )
	상판_수량2 = models.FloatField ( default= 0 )

	HD_기타층_Type = models.TextField( null=True, blank=True)
	HD_기타층_도면번호 = models.TextField( null=True, blank=True)
	HD_기타층_소재 = models.TextField( null=True, blank=True)
	HD_기타층_사양 = models.TextField( null=True, blank=True)

	HD_기준층_Type = models.TextField( null=True, blank=True)
	HD_기준층_도면번호 = models.TextField( null=True, blank=True)
	HD_기준층_소재 = models.TextField( null=True, blank=True)
	HD_기준층_사양 = models.TextField( null=True, blank=True)

	CD_Type = models.TextField( null=True, blank=True)
	CD_도면번호 = models.TextField( null=True, blank=True)
	CD_소재 = models.TextField( null=True, blank=True)
	CD_사양 = models.TextField( null=True, blank=True)

	CW_Type = models.TextField( null=True, blank=True)
	CW_도면번호 = models.TextField( null=True, blank=True)
	CW_소재 = models.TextField( null=True, blank=True)
	CW_사양 = models.TextField( null=True, blank=True)

	상판_Type = models.TextField( null=True, blank=True)
	상판_도면번호 = models.TextField( null=True, blank=True)
	상판_소재 = models.TextField( null=True, blank=True)
	상판_사양 = models.TextField( null=True, blank=True)

	표시순서 = models.IntegerField(default=0)

class Process(models.Model):

	작지Process_fk = models.ForeignKey( 작지.Process , on_delete=models.CASCADE, null=True, blank=True )

	생산처 = models.CharField(max_length=20,  null=True, blank=True)
	적용 = models.TextField( null=True, blank=True)
	소재 = models.CharField(max_length=50,  null=True, blank=True)
	치수 = models.CharField(max_length=50,  null=True, blank=True)

	구분 = models.CharField(max_length=20,  null=True, blank=True)
	수량 = models.IntegerField(default=0 )

	치수_두께 = models.FloatField(null=True, blank=True)
	치수_가로 = models.IntegerField(null=True, blank=True)
	치수_세로 = models.IntegerField(null=True, blank=True)

	대표Process = models.TextField(null=True, blank=True)
	상세Process = models.TextField(null=True, blank=True)
	출하처 = models.CharField(max_length=20,  null=True, blank=True)

	비고 = models.TextField(blank=True, null=True) 
	확정 = models.BooleanField ( blank=True, null=True )
	
	표시순서 = models.IntegerField(default=0)

	def save(self, *args, **kwargs):
		if hasattr(self, '치수') and self.치수 :
			치수 = self.치수.upper()
			if 치수 and 치수.count('X') == 2:
				self.치수 = 치수
				self.치수_두께 = float(치수.split('X')[0])
				self.치수_가로 = int(치수.split('X')[1])
				self.치수_세로 = int(치수.split('X')[2])
				print (self.치수)
		
		super().save(*args, **kwargs) 
		return self

class SPG_Table(models.Model):
	작지_process_fk = models.ForeignKey( 작지.Process , on_delete=models.CASCADE, null=True, blank=True)
	품번  = models.CharField(max_length=50, null=True, blank=True )
	측판폭_W  = models.CharField(max_length=50, null=True, blank=True )
	소재폭_W0  = models.CharField(max_length=50, null=True, blank=True )
	길이_L  = models.CharField(max_length=50, null=True, blank=True )
	소재길이_A0  = models.CharField(max_length=50, null=True, blank=True )
	밴딩W_T  =  models.TextField(null=True, blank=True)
	밴딩A_T  =  models.TextField(null=True, blank=True)
	W1  = models.CharField(max_length=50, null=True, blank=True )
	A1  = models.CharField(max_length=50, null=True, blank=True )
	W2  = models.CharField(max_length=50, null=True, blank=True )
	A2  = models.CharField(max_length=50, null=True, blank=True )
	W3  = models.CharField(max_length=50, null=True, blank=True )
	A3  = models.CharField(max_length=50, null=True, blank=True )
	대표Process = models.CharField(max_length=200, null=True, blank=True )
	상세Process = models.CharField(max_length=200, null=True, blank=True )
	표시순서 = models.IntegerField(default=1)

class SPG(models.Model):
	file1_fk = models.ForeignKey(SPG_file, on_delete=models.CASCADE, null=True, blank=True, related_name='file1')
	file2_fk = models.ForeignKey(SPG_file, on_delete=models.CASCADE, null=True, blank=True, related_name='file2')
	spg_table_fks = models.ManyToManyField(SPG_Table)

	job_name = models.CharField(max_length=50,  null=True, blank=True)
	proj_No = models.CharField(max_length=30,  null=True, blank=True)
	호기 = models.TextField(null=True, blank=True)
	비고 = models.TextField(null=True, blank=True)
	도면번호 = models.CharField( max_length=50, null=True, blank=True )

class 생산지시(models.Model):
	작업지침_fk= models.ForeignKey ( 작지.작업지침, on_delete=models.CASCADE, null=True, blank=True )
	NCR_fk= models.ForeignKey ( 품질경영.NCR, on_delete=models.CASCADE, null=True, blank=True )
	JAMB_발주정보_fk = models.ForeignKey( JAMB_발주정보, on_delete=models.SET_NULL, null=True, blank=True)

	tab_made_fks = models.ManyToManyField ( TAB_Made_file, related_name='tab_made+', blank=True)
	도면정보_fks = models.ManyToManyField( 도면정보, related_name='도면정보+', blank=True)
	process_fks = models.ManyToManyField( Process , related_name='Process+', blank=True	) 
	spg_fks = models.ManyToManyField( SPG, related_name='SPG+', blank=True)
	# spg생산지시서_fks = models.ManyToManyField( spg생산지시_file, related_name='spg생산')

	생산형태 = models.CharField(max_length=20,  null=True, blank=True)
	고객사 = models.CharField(max_length=20,  null=True, blank=True)
	구분 = models.CharField(max_length=20,  null=True, blank=True)
	### HTM
	Job_Name = models.CharField(max_length=50,  null=True, blank=True)
	Proj_No = models.CharField(max_length=30,  null=True, blank=True)
	총수량 = models.IntegerField (default=0)
	지시수량 = models.IntegerField (default=0)
	차수 = models.IntegerField (default=1)
	생산지시일 = models.DateField(  blank=True, null=True)
	소재발주일 = models.DateField(  blank=True, null=True)

	is_배포 = models.BooleanField(default=False)
	is_valid = models.BooleanField(default=False)

	### SPG
	SPG_호기 = models.TextField( blank=True, null=True )
	SPG_도면번호 = models.CharField(max_length=200,  null=True, blank=True)
	SPG_비고 = models.TextField( blank=True, null=True )    
  
	작성일 = models.DateField(  blank=True, null=True)
	작성자 = models.CharField(max_length=20,  null=True, blank=True)
	작성자_fk =  models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING,  null=True, blank=True, related_name='_생산지시_작성자_fk')

	진행현황_htm = models.CharField(max_length=20,  null=True, blank=True)
	진행현황_jamb = models.CharField(max_length=20,  null=True, blank=True)

	is_계획반영_htm = models.BooleanField(  blank=True, null=True)
	is_계획반영_jamb = models.BooleanField( blank=True, null=True )

	#ECO 관련 추가됨
	변경사유_내용 = models.TextField(null=True, blank=True)
	Rev = models.IntegerField(default=1)
	prev_생지 = models.ForeignKey( 'self', on_delete=models.CASCADE, null=True, blank=True )

	### django-simple-history
	history = HistoricalRecords()

	# def save(self, *args, **kwargs):
	#     # self.결재일 = timezone.now()
	#     # self.진행현황 = self._get_진행현황()
	#     super().save(*args, **kwargs) 
	#     if self.진행현황_htm == '배포' or self.진행현황_jamb == '배포':
	#         from 생산관리.models import 생산계획관리
	#         self._update( 생산계획관리)
	#         생산계획관리.objects.create

	# def _update(self, Model:models.Model, updateDict:dict ={} ) -> None:
	#     """ Model에 update함."""
	#     queryDict = {}
	#     # updateDict['생산지시_fk'] = self
	#     queryDict['생산지시_fk'] = self
	#     updateDict['납기일_Door'] = self.도면정보_fks.all()[0].납기일_Door
	#     updateDict['납기일_Cage'] = self.도면정보_fks.all()[0].납기일_Cage
	#     updateDict['납기일_JAMB'] = self.JAMB_발주정보_fk.출하요청일

	#     _instance, _created = Model.objects.get_or_create(**queryDict)
	#     # https://stackoverflow.com/questions/2696797/how-to-save-django-object-using-dictionary
	#     _instance.__dict__.update(updateDict)
	#     _instance.save()
	
	# def _get_진행현황(self):
	#     return 'test'
	#     print (self.결재내용_fks.count() )
	#     if ( not self.결재내용_fks.count() ): return '작성중'
		
	#     for 결재instance in self.결재내용_fks.all() :
	#         if ( 결재instance.결재의견 is not None ) :
	#             if( not 결재instance.결재의견 ): return '반려'

	#     for 결재instance in self.결재내용_fks.all() :
	#         if ( 결재instance.결재의견 is None) : return '진행중'

	#     return '완료'        

	
class Group생산지시 ( models.Model):
	작업지침_fk= models.ForeignKey ( 작지.작업지침, on_delete=models.CASCADE, null=True, blank=True )
	group = models.ManyToManyField( 생산지시, blank=True , related_name='group+')        
	잔여El수량 = models.IntegerField (blank=True, null=True)
	완료일자 = models.DateTimeField( null=True)

	def save(self, *args, **kwargs):
		if self.잔여EL수량 == 0 : self.완료일자 = timezone.now()
	   
		super().save(*args, **kwargs) 
		return self
