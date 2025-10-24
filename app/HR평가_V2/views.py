"""
Views for 샘플관리 APIs
"""
from drf_spectacular.utils import (
	extend_schema_view,
	extend_schema,
	OpenApiParameter,
	OpenApiTypes,
)

from rest_framework import (
	viewsets,
	mixins,
	status,
)
# from rest_framework.pagination import PageNumberPagination

from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime, date,time, timedelta
from django.http import QueryDict
### https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
from django.forms.models import model_to_dict
from django.db.models import Count, Sum , functions, Q, QuerySet, Max
from django.db import transaction

import os
import json
import copy
import pandas as pd
import numpy as np


from . import serializers, models, models_old, customfilters
# from util.customfilters import *
import util.utils_func as Util
from users.models import User, Api_App권한, Api_App권한_User_M2M

import logging, traceback
logger = logging.getLogger('HR평가_V2')

class OLD_Copy_View(APIView):
	""" 이 view는 HR평가( 이전 V1) 에서 HR평가_V2로 기 실시했던 평가 설정을 복사하는 기능입니다.  
	    따라서, 1회만 실행하면 됩니다. 
	1. 평가설정 복사
	2. 평가체계 복사
	3. 역량평가사전 복사 및 매핑 저장
	4. 역량평가항목 생성 (차수별 + 조건 분기)
	"""

	@transaction.atomic
	def get(self, request, *args, **kwargs):
		from django.forms.models import model_to_dict
		import HR평가.models as HR평가_models
		

		# 1. 평가설정 복사
		_instance평가설정 = HR평가_models.평가설정_DB.objects.get(id=38)
		원본_dict = model_to_dict(_instance평가설정, exclude=['id', '등록자_fk'])
		생성된_설정_instance = models.평가설정_DB.objects.create(
			**원본_dict,
			등록자_fk=_instance평가설정.등록자_fk,
		)

		# 2. 평가체계 복사 - V1 데이터를 먼저 완전히 evaluate
		qs평가체계 = list(
			HR평가_models.평가체계_DB.objects.filter(평가설정_fk=_instance평가설정)
		)

		for _instance in qs평가체계:
			# ✅ 이 시점에서 DB 접근 없음
			원본_dict = model_to_dict(
				_instance,
				exclude=['id', '평가설정_fk', '평가자', '피평가자']
			)
			원본_dict.update({
				'평가설정_fk': 생성된_설정_instance,
				'평가자': _instance.평가자,
				'피평가자': _instance.피평가자,
				'is_submit': True  # ✅ V2에만 존재
			})
			models.평가체계_DB.objects.create(**원본_dict)

		# 3. 역량사전 복사
		역량사전_매핑 = {}
		qs역량사전 = list(HR평가_models.역량평가사전_DB.objects.all())
		for _instance in qs역량사전:
			원본_dict = model_to_dict(_instance, exclude=['id', '등록자_fk'])
			원본_dict['등록자_fk'] = _instance.등록자_fk
			복사된 = models.역량평가사전_DB.objects.create(**원본_dict)
			역량사전_매핑[_instance.id] = 복사된

		# 4. 항목 생성
		for 차수 in range(생성된_설정_instance.총평가차수):
			for 원본 in qs역량사전:
				if 차수 == 0 and 원본.구분 == '리더십역량':
					continue
				models.역량평가_항목_DB_V2.objects.create(
					평가설정_fk=생성된_설정_instance,
					항목=역량사전_매핑[원본.id],
					차수=차수
				)

		return Response({'message': '복사 완료!'})	

    
class 지난평가결과_copy_to_V2_View(APIView):
	""" 이 view는 HR평가( 이전 V1) 에서 HR평가_V2로 기 실시했던 평가 결과를 V2 형태로 복사하는 기능입니다.  
	    따라서, 1회만 실행하면 됩니다. 
	1. 평가설정 복사
	2. 평가체계 복사
	3. 역량평가사전 복사 및 매핑 저장
	4. 역량평가항목 생성 (차수별 + 조건 분기)
	"""

	def is_세부평가(self, _v1_평가결과_instance):
		from HR평가.models import 평가결과_DB
		_v1_평가결과_instance : 평가결과_DB = _v1_평가결과_instance
		return _v1_평가결과_instance.ability_m2m.exists() or _v1_평가결과_instance.perform_m2m.exists() or _v1_평가결과_instance.special_m2m.exists()

	@transaction.atomic
	def get(self, request, *args, **kwargs):
		try:
	
			from django.forms.models import model_to_dict
			import HR평가.models as HR평가_models
			
			# 1. 평가설정 Instance 가져오기
			_v1_instance평가설정 = HR평가_models.평가설정_DB.objects.get(id=38) ### 불변이므로 id 로 가져옴
			_v2_instance평가설정 = models.평가설정_DB.objects.get( 제목 = _v1_instance평가설정.제목 ) #### 변동이므로 제목으로 가져옴
			print ( _v2_instance평가설정 )

			# 2. 평가결과 저장하기 위한 생성 (즉, 평가설정에서 평가start 개념)
			_v1_qs평가체계 = HR평가_models.평가체계_DB.objects.filter( 평가설정_fk = _v1_instance평가설정, is_참여 = True )
			print ( '_v1_qs평가체계', _v1_qs평가체계.count(), _v1_qs평가체계 )
			####  평가체계에 따른  역량평가_DB, 성과평가_DB, 특별평가_DB 생성은 이미 되어 있음
			_v2_qs평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk = _v2_instance평가설정 , is_참여 = True )
			print ( '_v2_qs평가체계', _v2_qs평가체계.count(), _v2_qs평가체계 )
			map_평가체계_v2_to_v1 : dict[int, any] = {} ### v2 평가체계 id 를 v1 평가체계 instance 로 매핑
			for _v2_instance평가체계 in _v2_qs평가체계:
				map_평가체계_v2_to_v1[_v2_instance평가체계.id] = _v1_qs평가체계.get( 
					평가설정_fk = _v1_instance평가설정,
					평가자 = _v2_instance평가체계.평가자,
					피평가자 = _v2_instance평가체계.피평가자,
					차수 = _v2_instance평가체계.차수,
				)


			#### v1 평가결과를 가져와서 v2로 저장		
			#### 평가체계는 구성되어 있지만, 모든 평가 결과는 없음. ==> 생성해야 함.
			for _v2_instance평가체계 in _v2_qs평가체계:
				### v1 평가결과 가져오기
				_v1_평가결과 = HR평가_models.평가결과_DB.objects.get( 평가체계_fk = map_평가체계_v2_to_v1[_v2_instance평가체계.id] )

				_v2_instance평가체계.is_submit = _v1_평가결과.is_submit
				_v2_instance평가체계.save()

				create_dict = {
					'평가체계_fk': _v2_instance평가체계,
					'평가종류': '개별' if _v2_instance평가체계.차수 <= 1 else '종합',
					'is_submit': _v1_평가결과.is_submit,
				}

				### v2 역량평가_DB, 성과평가_DB, 특별평가_DB 생성
				_v2_instance_역량평가 = models.역량평가_DB_V2.objects.create( **create_dict, 평가점수 = _v1_평가결과.역량점수 )
				_v2_instance_성과평가 = models.성과평가_DB_V2.objects.create( **create_dict, 평가점수 = _v1_평가결과.성과점수 )
				_v2_instance_특별평가 = models.특별평가_DB_V2.objects.create( **create_dict, 평가점수 = _v1_평가결과.특별점수 )

				if self.is_세부평가(_v1_평가결과):
					map_역량평가_항목_v1_to_v2:dict[int, any] = {
						_v1_항목.id : models.역량평가_항목_DB_V2.objects.filter(
							평가설정_fk = _v2_instance평가설정,
							항목 = models.역량평가사전_DB.objects.get(
								구분 = _v1_항목.구분,
								항목 = _v1_항목.항목,
								정의 = _v1_항목.정의,
							),
						)
						for _v1_항목 in HR평가_models.역량평가사전_DB.objects.all()	
					}					
					차수 = _v1_평가결과.평가체계_fk.차수
					### 세부 역량평가 저장
					for _v1_역량평가 in _v1_평가결과.ability_m2m.all():			
						try:
							if 차수 == 0: ## 본인평가 일때는 차수 0 으로 저장
								최대_평가차수 = models.평가체계_DB.objects.filter( 
									평가설정_fk = _v2_instance평가설정, 
									평가자 = _v1_평가결과.평가체계_fk.평가자
									).aggregate(Max('차수'))['차수__max']
								항목_instance = map_역량평가_항목_v1_to_v2[_v1_역량평가.fk.id].get(차수 = 최대_평가차수)
							else:
								항목_instance = map_역량평가_항목_v1_to_v2[_v1_역량평가.fk.id].get(차수 = 차수)
						except:
							print ( f'역량평가항목이 없습니다. {_v2_instance평가설정.id} {_v1_역량평가.fk.id}' )
							pass
							# raise Exception ( f'역량평가항목이 없습니다.  {_v1_역량평가.fk.id} -- {_v1_평가결과.평가체계_fk.차수} -- {_v1_역량평가.fk.구분} -- {_v1_역량평가.fk.항목}' )

						models.세부_역량평가_DB_V2.objects.create(
							역량평가_fk = _v2_instance_역량평가,
							항목 = 항목_instance,
							평가점수 = _v1_역량평가.평가점수
						)
					### 세부 성과평가 저장
					for _v1_성과평가 in _v1_평가결과.perform_m2m.all():
						_v1_성과평가 : HR평가_models.성과_평가_DB
						models.세부_성과평가_DB_V2.objects.create(
							성과평가_fk = _v2_instance_성과평가,
							과제명 = _v1_성과평가.과제명,
							과제목표 = _v1_성과평가.과제목표,
							성과 = _v1_성과평가.성과,
							목표달성률 = _v1_성과평가.목표달성률,
							실행기간 = _v1_성과평가.실행기간,
							가중치 = _v1_성과평가.가중치,
							평가점수 = _v1_성과평가.평가점수
						)
					### 세부 특별평가 저장
					for _v1_특별평가 in _v1_평가결과.special_m2m.all():
						_v1_특별평가 : HR평가_models.특별_평가_DB
						models.세부_특별평가_DB_V2.objects.create(
							특별평가_fk = _v2_instance_특별평가,
							구분 = _v1_특별평가.구분,
							성과 = _v1_특별평가.성과,
							가중치 = _v1_특별평가.가중치,
							평가점수 = _v1_특별평가.평가점수
						)
				



			return Response({'message': '평가결과 migration 완료!'})
		
		except HR평가_models.평가체계_DB.DoesNotExist:
			print(f"[X] 매칭 실패: V2 ID={_v2_instance평가체계.id}")
			print(f"    평가자: {_v2_instance평가체계.평가자}")
			print(f"    피평가자: {_v2_instance평가체계.피평가자}")
			print(f"    차수: {_v2_instance평가체계.차수}")
			print("    ---- v1 후보군 ----")
			for v1 in _v1_qs평가체계.filter(
				피평가자=_v2_instance평가체계.피평가자
			):
				print(f"        v1 id={v1.id}, 평가자={v1.평가자}, 차수={v1.차수}")
			raise

		except Exception as e:
			print ( e )
			print ( traceback.format_exc() )
			return Response({'message': '평가결과 migration 실패!'})
		

class Migration_Init_View(APIView):
	
	@transaction.atomic
	def get(self, request, *args, **kwargs):

		try:			
			import HR평가.models as HR평가_models
			
			# 1. 평가설정 Instance 가져오기
			_v1_instance평가설정 = HR평가_models.평가설정_DB.objects.get(id=38) ### 불변이므로 id 로 가져옴
			_v2_instance평가설정 = models.평가설정_DB.objects.get( 제목 = _v1_instance평가설정.제목 ) #### 변동이므로 제목으로 가져옴
			print ( _v2_instance평가설정 )

			models.역량평가_DB_V2.objects.filter(평가체계_fk__평가설정_fk = _v2_instance평가설정).delete()
			models.성과평가_DB_V2.objects.filter(평가체계_fk__평가설정_fk = _v2_instance평가설정).delete()
			models.특별평가_DB_V2.objects.filter(평가체계_fk__평가설정_fk = _v2_instance평가설정).delete()

			qs_세부_역량평가 = models.세부_역량평가_DB_V2.objects.filter(역량평가_fk__평가체계_fk__평가설정_fk = _v2_instance평가설정)
			qs_세부_성과평가 = models.세부_성과평가_DB_V2.objects.filter(성과평가_fk__평가체계_fk__평가설정_fk = _v2_instance평가설정)
			qs_세부_특별평가 = models.세부_특별평가_DB_V2.objects.filter(특별평가_fk__평가체계_fk__평가설정_fk = _v2_instance평가설정)

			print(qs_세부_역량평가.count())
			print(qs_세부_성과평가.count())
			print(qs_세부_특별평가.count())
			# qs_세부_역량평가.delete()
			# qs_세부_성과평가.delete()
			# qs_세부_특별평가.delete()

			return Response({'message': '평가결과  migration 초기화 완료!'})
		
		except Exception as e:
			print ( e )
			print ( traceback.format_exc() )
			return Response({'message': '평가결과  migration 초기화 실패!'})



class 역량평가사전_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.역량평가사전_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.역량평가사전_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['구분','항목','정의']
	# filterset_class =  역량평가사전_DB_Filter


	def get_queryset(self):
		return  self.MODEL.objects.order_by('구분','항목','정의')


class 평가설정_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.평가설정_DB
	queryset = MODEL.objects.order_by('-id')	
	serializer_class = serializers.평가설정_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['제목']
	# filterset_class =  평가설정_DB_Filter

	@action(detail=True, methods=['get'], url_path='평가설정_copy_create')
	def 평가설정_copy_create(self, request, *args, **kwargs):
		instance : models.평가설정_DB = self.get_object()
		logger.info ( f'평가설정_copy_create: {instance.제목}' )
		with transaction.atomic():
			### 1 . 평가설정_db copy&create
			instance_new = models.평가설정_DB.objects.create(
				제목=f'복사본 : {instance.제목}',

				시작=date.today(),
				종료=date.today() + timedelta(days=7),
				총평가차수=instance.총평가차수,
				점유_역량=instance.점유_역량,
				점유_성과=instance.점유_성과,
				점유_특별=instance.점유_특별,
				차수별_점유=instance.차수별_점유,
				차수별_유형=instance.차수별_유형,
				등록자_fk=request.user,
				is_시작=False,
				is_종료=False,
			)

			### 2. 평가체계 copy & create
			qs = models.평가체계_DB.objects.filter( 평가설정_fk=instance , 피평가자__is_active=True )
			new_objs = [
				models.평가체계_DB(
					평가설정_fk=instance_new ,
					평가자=obj.평가자,
					피평가자=obj.피평가자,
					차수=obj.차수,
					is_참여=obj.is_참여
				)
				for obj in qs
			]
			models.평가체계_DB.objects.bulk_create(new_objs)
			
			#### 3. 역량평가항목 생성 (차수별 + 조건 분기)
			qs_역량평가항목 = models.역량평가_항목_DB_V2.objects.filter( 
				평가설정_fk=instance
				 )
			for _inst_역량평가항목  in qs_역량평가항목:
				models.역량평가_항목_DB_V2.objects.create(
					평가설정_fk=instance_new,
					항목=_inst_역량평가항목.항목,
					차수=_inst_역량평가항목.차수
				)

		return Response ( status=status.HTTP_200_OK, 
				   data = self.serializer_class(instance_new).data
				   )

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):		
		return super().create(request, *args, **kwargs )

	def update(self, request, *args, **kwargs):
		try:
			logger.info ( f'update: {request.data}' )
			instance = self.get_object()
			is_시작 = request.data.get('is_시작', False)			
			is_종료 = request.data.get('is_종료', False)
			logger.info ( f'is_시작: {is_시작}, is_종료: {is_종료}, {type(is_시작)}, {type(is_종료)}' )
			if instance.is_시작 == False and (is_시작 == 'True' or is_시작):
				
				qs평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk = instance )
				with transaction.atomic():
					####  평가체계에 따른  역량평가_DB, 성과평가_DB, 특별평가_DB 생성
					for 평가체계 in qs평가체계:
						####1. 역량평가_DB 생성
						models.역량평가_DB_V2.objects.get_or_create( 
							평가체계_fk = 평가체계 , 평가종류=instance.차수별_유형[str(평가체계.차수)]
							)
						####2. 성과평가_DB 생성
						models.성과평가_DB_V2.objects.get_or_create( 
							평가체계_fk = 평가체계 , 평가종류=instance.차수별_유형[str(평가체계.차수)]
							)
						####3. 특별평가_DB 생성
						models.특별평가_DB_V2.objects.get_or_create( 
							평가체계_fk = 평가체계 , 평가종류=instance.차수별_유형[str(평가체계.차수)]
							)
					
					#### 본인평가 : 세부_역량평가_DB, 세부_성과평가_DB, 세부_특별평가_DB 생성
					qs_본인평가 = models.평가체계_DB.objects.filter( 평가설정_fk = instance, 차수=0, is_참여=True )
					qs_상급자평가 = models.평가체계_DB.objects.filter( 평가설정_fk = instance, 차수__gte=1, is_참여=True )
					for 본인평가 in qs_본인평가:
						평가자 = 본인평가.평가자
						최대_평가차수 = models.평가체계_DB.objects.filter( 
							평가설정_fk = instance, 평가자 = 평가자 ).aggregate(Max('차수'))['차수__max']
						### 세부_역량평가_DB는 최대_평가차수에 맞게 역량평가 항목을 가져와서 생성함
						qs_역량평가_항목 = models.역량평가_항목_DB_V2.objects.filter( 평가설정_fk = instance, 차수 = 최대_평가차수 )
						역량평가_DB_obj, _created = models.역량평가_DB_V2.objects.get_or_create( 평가체계_fk = 본인평가 )
						for 항목 in qs_역량평가_항목:
							models.세부_역량평가_DB_V2.objects.get_or_create( 
								역량평가_fk = 역량평가_DB_obj , 
								항목 = 항목
							)

						### 세부_성과평가 항목을 초기 1개만 가져와서 생성함
						성과평가_DB_obj = models.성과평가_DB_V2.objects.get( 평가체계_fk = 본인평가 )
						models.세부_성과평가_DB_V2.objects.get_or_create( 
							성과평가_fk = 성과평가_DB_obj , 
						)
						### 세부_특별평가 항목을 초기 1개만 가져와서 생성함
						특별평가_DB_obj = models.특별평가_DB_V2.objects.get( 평가체계_fk = 본인평가 )
						models.세부_특별평가_DB_V2.objects.get_or_create( 
							특별평가_fk = 특별평가_DB_obj , 
						)
					#### 상급자 평가 : 생성 없음 ===> 본인 평가에 따른 상급자 평가 생성 (평가 체계 및 평가종류에 따라서)
					self._activate_api_app권한( _inst_권한= Api_App권한.objects.get( id = 167 ),  qs평가체계=qs_본인평가 )
					self._activate_api_app권한( _inst_권한= Api_App권한.objects.get( id = 168 ),  qs평가체계=qs_상급자평가 )

			if instance.is_시작 == True and  (is_시작 == 'False'):
				qs평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk = instance )
				with transaction.atomic():
					models.역량평가_DB_V2.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					models.성과평가_DB_V2.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					models.특별평가_DB_V2.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					

					
			if instance.is_종료 == False and (is_종료 == 'True' or is_종료):
				self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 167 ) )
				self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 168 ) )

			return super().update(request, *args, **kwargs )
		except Exception as e:
			logger.error(f"Error during update: {str(e)}")
			logger.error(traceback.format_exc())
			return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
	
	def _activate_api_app권한(self, _inst_권한:Api_App권한,  qs평가체계:QuerySet[models.평가체계_DB]  ):

		with transaction.atomic():
			Api_App권한_User_M2M.objects.get_or_create( app_권한 = _inst_권한 , user_id =1 )
			for 평가체계 in qs평가체계:
				Api_App권한_User_M2M.objects.get_or_create( app_권한 = _inst_권한, user = 평가체계.평가자 )

			_inst_권한.is_Run = True
			_inst_권한.save()

	def _deactivate_api_app권한(self, _inst_권한:Api_App권한 ):
		try:
			with transaction.atomic():
				Api_App권한_User_M2M.objects.exclude( user_id = 1 ).filter( app_권한 = _inst_권한 ).delete()
				_inst_권한.is_Run = False
				_inst_권한.save()
		except Exception as e:
			logger.error(f"Error during deactivate_api_app권한: {str(e)}")
			logger.error(traceback.format_exc())
			return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

	def destroy(self, request, *args, **kwargs):
		self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 167 ) )
		self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 168 ) )
		
		return super().destroy(request, *args, **kwargs)



class 평가체계_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.평가체계_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가체계_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	filterset_fields = ['평가설정_fk']
	# search_fields =['제목']
	# # filterset_class =  customfilters.평가체계_DB_Filter

	def get_queryset(self):
		# active_평가설정 = models.평가설정_DB.objects.get( is_시작=True, is_종료=False )
		return  ( self.MODEL.objects
				.select_related('평가설정_fk')
				.order_by('-id')
				)
	
	@action(detail=False, methods=['post'], url_path='bulk_update')
	def bulk_update(self, request, *args, **kwargs):
		update_list = json.loads(request.data.get('update_list', '[]'))

		if not isinstance(update_list, list) or not update_list:
			return Response({"error": "No valid update_list provided"}, status=status.HTTP_400_BAD_REQUEST)

		logger.info(f"bulk_update: {update_list}")

		success_count = 0
		failed_items = []
		try:
			with transaction.atomic():
				for item in update_list:
					obj_id = item.get('id', -1)
					if  obj_id == -1:
						self.MODEL.objects.create(
							평가설정_fk_id= item.get('평가설정_fk'),
							평가자_id=item.get('평가자'),
							피평가자_id=item.get('피평가자'),
							차수=item.get('차수'),
							is_참여=item.get('is_참여', True)
						)

					try:
						obj = self.MODEL.objects.select_for_update().get(id=obj_id)
						obj.평가자_id = item.get('평가자')
						obj.is_참여 = item.get('is_참여', True)					
						obj.save()
						success_count += 1
					except self.MODEL.DoesNotExist:
						failed_items.append({'item': item, 'reason': 'Object not found'})
					except Exception as e:
						failed_items.append({'item': item, 'reason': str(e)})

			return Response({
				"result": "ok",
				"updated": success_count,
				"failed": failed_items,
			}, status=status.HTTP_200_OK)
		except Exception as e:
			logger.error(f"Error during bulk_update: {str(e)}")
			logger.error(traceback.format_exc())
			return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
		
	def 초기화_및_점수초기화(self, instance: models.평가체계_DB):
		"""해당 평가체계 관련 평가 및 세부평가 초기화"""
		models.역량평가_DB_V2.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)
		models.성과평가_DB_V2.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)
		models.특별평가_DB_V2.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)

		역 = models.역량평가_DB_V2.objects.filter(평가체계_fk=instance).first()
		성 = models.성과평가_DB_V2.objects.filter(평가체계_fk=instance).first()
		특 = models.특별평가_DB_V2.objects.filter(평가체계_fk=instance).first()

		if 역:
			models.세부_역량평가_DB_V2.objects.filter(역량평가_fk=역).delete()
		if 성:
			models.세부_성과평가_DB_V2.objects.filter(성과평가_fk=성).delete()
		if 특:
			models.세부_특별평가_DB_V2.objects.filter(특별평가_fk=특).delete()


	def handle_action_제출취소(self, instance: models.평가체계_DB, is_본인평가: bool):
		instance.is_submit = False
		instance.save(update_fields=['is_submit'])

		if is_본인평가:
			qs_상급자 = models.평가체계_DB.objects.filter(
				평가설정_fk=instance.평가설정_fk,
				피평가자=instance.피평가자,
				차수__gte=1
			)
			for 상급자 in qs_상급자:
				상급자.is_submit = False
				상급자.save(update_fields=['is_submit'])
				self.초기화_및_점수초기화(상급자)


	@transaction.atomic
	@action(detail=True, methods=['get'], url_path='action_제출취소')
	def action_제출취소(self, request, *args, **kwargs):
		try:
			instance = self.get_object()
			is_본인평가 = (instance.차수 == 0)
			self.handle_action_제출취소(instance, is_본인평가)
			return Response(status=status.HTTP_200_OK, data={'result': 'ok'})
		except Exception as e:
			logger.error(f"Error during action_제출취소: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)})


	@transaction.atomic
	@action(detail=True, methods=['get'], url_path='action_초기화_및_제출취소')
	def action_초기화_및_제출취소(self, request, *args, **kwargs):
		try:
			instance = self.get_object()
			is_본인평가 = (instance.차수 == 0)
			self.handle_action_제출취소(instance, is_본인평가)
			self.초기화_및_점수초기화(instance)
			return Response(status=status.HTTP_200_OK, data={'result': 'ok'})
		except Exception as e:
			logger.error(f"Error during action_초기화_및_제출취소: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)})


	@transaction.atomic
	def update(self, request, *args, **kwargs):
		instance : models.평가체계_DB = self.get_object()
		logger.info(f"instance: {instance}")

		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if (is_참여 :=request.data.get('is_참여', False) ): 

				for 상급평가_instance in models.평가체계_DB.objects.filter( 평가설정_fk = instance.평가설정_fk, 피평가자 = instance.평가자, 차수__gte=1 ):
					상급평가_instance.is_참여 = is_참여
					상급평가_instance.save(update_fields=['is_참여'])
		
		return super().update(request, *args, **kwargs )
	
	def list(self, request, *args, **kwargs):
		queryset = self.filter_queryset(self.get_queryset())

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)
	


class 역량평가_항목_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.역량평가_항목_DB_V2
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.역량평가_항목_DB_Serializer_V2
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가설정_fk']
	# filterset_class =  customfilters.역량평가_항목_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def list(self, request, *args, **kwargs):
		params = request.query_params
		logger.info ( params )
		평가설정_fk = params.get('평가설정_fk')
		평가설정_instance = models.평가설정_DB.objects.get( id = 평가설정_fk )
		총평가차수 = 평가설정_instance.총평가차수
		if not 평가설정_fk:
			return Response({"error": "평가설정_fk is required"}, status=400)

		# 기존 DB 항목 조회
		existing_items = self.MODEL.objects.filter(
			평가설정_fk_id=평가설정_fk,
			차수__in=range(총평가차수+1)
		)
		logger.info(f"Existing items: {existing_items}")
		logger.info(f"Existing items: {existing_items.count()}")
		existing_map = {
			f"{item.차수}_{item.항목.id}": item for item in existing_items if item.항목 is not None
		}
		logger.info(f"Existing map: {existing_map}")
		# 사전 전체 항목 기준으로 출력
		전체_역량평가사전항목 = models.역량평가사전_DB.objects.all()
		result_data = []

		for 차수 in range(총평가차수+1):
			for 항목_instance in 전체_역량평가사전항목:
				key = f"{차수}_{항목_instance.id}"
				if key in existing_map:
					# 이미 저장된 항목은 serializer로
					serialized = self.serializer_class(existing_map[key]).data
				else:
					# 없는 항목은 기본값으로 구성
					serialized = {
							"id": -1,
							"평가설정_fk": 평가설정_fk,
							"차수": 차수,
							"항목": 항목_instance.id,
							"항목_이름": 항목_instance.항목,
							"구분": 항목_instance.구분,
							"정의": 항목_instance.정의
						}
				result_data.append(serialized)
		result_data.sort(key=lambda x: (x['차수'], x['구분'], x['항목_이름']))

		return Response(result_data)
		
	@action(detail=False, methods=['post'], url_path='bulk')
	def bulk(self, request, *args, **kwargs):
		logger.info(f"Request data: {request.data}")
		_list = json.loads(request.data.get('_list', []))
		평가설정_fk = request.data.get('평가설정_fk', False)
		if not isinstance(_list, list) or not 평가설정_fk:
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'No data provided'})
		
		valid_ids = set()
		try:
			with transaction.atomic():
				for _inst in _list:
					if _inst.get('id') == -1:
						created =models.역량평가_항목_DB_V2.objects.create( 
							평가설정_fk_id = 평가설정_fk, 차수 = _inst.get('차수'), 항목_id = _inst.get('항목') 
							)
						valid_ids.add(created.id)
					else:
						models.역량평가_항목_DB_V2.objects.filter( id = _inst.get('id') ).update( 
							평가설정_fk_id = 평가설정_fk, 차수 = _inst.get('차수'), 항목_id = _inst.get('항목') 
							)
						valid_ids.add(_inst.get('id'))

				### 삭제 : valid_ids 에 없는 항목 삭제 , 만약 empty 라면 .exclude(id__in=[]) → 전체 항목을 포함 (즉, 아무 id도 제외되지 않음)
				models.역량평가_항목_DB_V2.objects.filter(평가설정_fk_id=평가설정_fk).exclude(id__in=valid_ids).delete()

			return Response(status=status.HTTP_200_OK, data={'result': 'ok'})
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})


def get_Nested_평가체계_serializer_data(평가체계_instance:models.평가체계_DB):
	try:
		평가설정_instance:models.평가설정_DB = 평가체계_instance.평가설정_fk 
		# 평가설정_instance = models.평가설정_DB.objects.get( id=평가체계_instance.평가설정_fk )
		차수 = 평가체계_instance.차수
		평가유형 = 평가설정_instance.차수별_유형[str(차수)]
		result = {}
		result['평가설정_data'] = serializers.평가설정_DB_Serializer(평가설정_instance, many=False).data
		result['평가체계_data'] = serializers.평가체계_DB_Serializer(평가체계_instance, many=False).data

		result.update( get_3대평가_serializer_data(평가체계_instance, 평가유형, 차수) )
		match 평가유형:
			case '개별':
				pass
			case '종합':
				pass
			case _:
				raise ValueError(f"평가유형 {평가유형} 은 존재하지 않습니다.")
			
		result['평가체계_data']['종합평가'] = get_종합평가_계산(평가체계_instance)
		print(f"result['평가체계_data']: {result['평가체계_data']}")
		return result
	except Exception as e:
		logger.error(f"Error during get_평가체계_serializer_data: {e}")
		logger.error(traceback.format_exc())
		return {}
	
def get_종합평가_계산(평가체계_instance:models.평가체계_DB) -> dict[str, float]:
	평가설정_instance:models.평가설정_DB = 평가체계_instance.평가설정_fk 
	# 평가설정_instance = models.평가설정_DB.objects.get( id=평가체계_instance.평가설정_fk )
	차수 = 평가체계_instance.차수
	평가유형 = 평가설정_instance.차수별_유형.get(str(차수))
	점유_역량 = 평가설정_instance.점유_역량
	점유_성과 = 평가설정_instance.점유_성과
	점유_특별 = 평가설정_instance.점유_특별
	
	# 역량평가_DB_instance = models.역량평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	# 성과평가_DB_instance = models.성과평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	# 특별평가_DB_instance = models.특별평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)

	역량평가_DB_instance = only_one_instance_by_recent_id(models.역량평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	성과평가_DB_instance = only_one_instance_by_recent_id(models.성과평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	특별평가_DB_instance = only_one_instance_by_recent_id(models.특별평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	
	종합평가 = 역량평가_DB_instance.평가점수 * 점유_역량 / 100 + 성과평가_DB_instance.평가점수 * 점유_성과 / 100 + 특별평가_DB_instance.평가점수 * 점유_특별 / 100
	return 종합평가
	return {'종합평가': 종합평가}
	
def only_one_instance_by_recent_id(model_class, query_condition: dict):
	qs = model_class.objects.filter(**query_condition).order_by('-id')
	count = qs.count()
	if count == 0:
		raise ValueError(f"{model_class.__name__}  {query_condition} 조회된 데이터가 없습니다.")
	elif count == 1:
		return qs.first()
	else:
		# 첫 번째 (최신) 인스턴스 제외한 나머지를 bulk delete
		ids_to_delete = qs.values_list('id', flat=True)[1:]
		model_class.objects.filter(id__in=ids_to_delete).delete()
		print(f"ids_to_delete: {ids_to_delete}")
		return qs.first()

		
def get_3대평가_serializer_data(평가체계_instance:models.평가체계_DB, 평가유형:str, 차수:int):
	역량평가_DB_instance = only_one_instance_by_recent_id(models.역량평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	성과평가_DB_instance = only_one_instance_by_recent_id(models.성과평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	특별평가_DB_instance = only_one_instance_by_recent_id(models.특별평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	# 역량평가_DB_instance = models.역량평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	# 성과평가_DB_instance = models.성과평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	# 특별평가_DB_instance = models.특별평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)

	역량평가_fk_api_datas = serializers.역량평가_DB_Serializer_V2(역량평가_DB_instance, many=False).data if 역량평가_DB_instance else None
	성과평가_fk_api_datas = serializers.성과평가_DB_Serializer_V2(성과평가_DB_instance, many=False).data if 성과평가_DB_instance else None	
	특별평가_fk_api_datas = serializers.특별평가_DB_Serializer_V2(특별평가_DB_instance, many=False).data if 특별평가_DB_instance else None

	if 평가유형 == '개별':
		_dict =  get_세부평가_serializer_data(평가체계_instance,  차수)
		역량평가_fk_api_datas['역량평가_api_datas'] = _dict['역량평가_api_datas']
		성과평가_fk_api_datas['성과평가_api_datas'] = _dict['성과평가_api_datas']
		특별평가_fk_api_datas['특별평가_api_datas'] = _dict['특별평가_api_datas']

	elif 평가유형 == '종합':
		pass
	else:
		raise ValueError(f"평가유형 {평가유형} 은 존재하지 않습니다.")
	return {
		'역량평가_fk': 역량평가_fk_api_datas,
		'성과평가_fk': 성과평가_fk_api_datas, 
		'특별평가_fk': 특별평가_fk_api_datas,
		}
	
def get_세부평가_serializer_data(평가체계_instance:models.평가체계_DB,  차수:int):
	역량평가_DB_instance = only_one_instance_by_recent_id(models.역량평가_DB_V2, {'평가체계_fk': 평가체계_instance})
	역량평가_항목_QS = models.세부_역량평가_DB_V2.objects.filter(역량평가_fk = 역량평가_DB_instance)
	피평가자 = 평가체계_instance.피평가자
	평가자 = 평가체계_instance.평가자
	피평가자_본인평가_평가체계 = models.평가체계_DB.objects.get( 평가설정_fk = 평가체계_instance.평가설정_fk, 평가자 = 피평가자, 차수 = 0 )

	if 역량평가_항목_QS.count() == 0:
		#### 본인 평가
		if 차수 == 0:
			최대_평가차수 =	models.평가체계_DB.objects.filter( 
								평가설정_fk = 평가체계_instance.평가설정_fk, 평가자 = 평가자 ).aggregate(Max('차수'))['차수__max']
			### 세부_역량평가_DB는 최대_평가차수에 맞게 역량평가 항목을 가져와서 생성함
			역량평가_DB_obj = models.역량평가_DB_V2.objects.get( 평가체계_fk = 평가체계_instance )
			for 항목 in models.역량평가_항목_DB_V2.objects.filter( 평가설정_fk = 평가체계_instance.평가설정_fk, 차수 = 최대_평가차수 ):
				models.세부_역량평가_DB_V2.objects.get_or_create( 
					역량평가_fk = 역량평가_DB_obj , 
					항목 = 항목
				)
			역량평가_항목_QS = models.세부_역량평가_DB_V2.objects.filter(역량평가_fk = 역량평가_DB_instance)
		
		#### 상급자 평가
		else:
			### 세부_역량평가_DB는 피평가자 본인평가의 역량평가 항목을 가져와서 생성함

			피평가자_역량평가_DB_obj = models.역량평가_DB_V2.objects.get( 평가체계_fk = 피평가자_본인평가_평가체계 )
			for 항목 in models.세부_역량평가_DB_V2.objects.filter( 역량평가_fk = 피평가자_역량평가_DB_obj  ):
				models.세부_역량평가_DB_V2.objects.get_or_create( 
					역량평가_fk = 역량평가_DB_instance , 
					항목 = 항목.항목,
					평가점수 = 0
				)
			역량평가_항목_QS = models.세부_역량평가_DB_V2.objects.filter(역량평가_fk = 역량평가_DB_instance)
	역량평가_serializer = serializers.세부_역량평가_DB_Serializer_V2(역량평가_항목_QS, many=True)	
	

	# logger.info(f"역량항목_api_datas: {역량평가_serializer.data}")

	성과평가_DB_instance = models.성과평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	성과평가_항목_QS = models.세부_성과평가_DB_V2.objects.filter(성과평가_fk = 성과평가_DB_instance)
	if 성과평가_항목_QS.count() == 0:
		#### 본인평가
		if 차수 == 0:
			models.세부_성과평가_DB_V2.objects.create( 성과평가_fk = 성과평가_DB_instance )
			성과평가_항목_QS = models.세부_성과평가_DB_V2.objects.filter(성과평가_fk = 성과평가_DB_instance)
		#### 상급자평가
		else:
			피평가자_성과평가_DB_obj = models.성과평가_DB_V2.objects.get( 평가체계_fk = 피평가자_본인평가_평가체계 )
			for 항목 in models.세부_성과평가_DB_V2.objects.filter( 성과평가_fk = 피평가자_성과평가_DB_obj  ):
				models.세부_성과평가_DB_V2.objects.get_or_create( 
					성과평가_fk = 성과평가_DB_instance , 
					과제명 = 항목.과제명,
					과제목표 = 항목.과제목표,
					성과 = 항목.성과,
					목표달성률 = 항목.목표달성률,
					실행기간 = 항목.실행기간,
					가중치 = 항목.가중치,
					평가점수 = 0
				)
			성과평가_항목_QS = models.세부_성과평가_DB_V2.objects.filter(성과평가_fk = 성과평가_DB_instance)
	성과평가_serializer = serializers.세부_성과평가_DB_Serializer_V2(성과평가_항목_QS, many=True)
	# logger.info(f"성과항목_api_datas: {성과평가_serializer.data}")

	특별평가_DB_instance = models.특별평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	특별평가_항목_QS = models.세부_특별평가_DB_V2.objects.filter(특별평가_fk = 특별평가_DB_instance)
	if 특별평가_항목_QS.count() == 0:
		#### 본인평가
		if 차수 == 0:
			models.세부_특별평가_DB_V2.objects.create( 특별평가_fk = 특별평가_DB_instance )
			특별평가_항목_QS = models.세부_특별평가_DB_V2.objects.filter(특별평가_fk = 특별평가_DB_instance)
		#### 상급자평가
		else:
			피평가자_특별평가_DB_obj = models.특별평가_DB_V2.objects.get( 평가체계_fk = 피평가자_본인평가_평가체계 )
			for 항목 in models.세부_특별평가_DB_V2.objects.filter( 특별평가_fk = 피평가자_특별평가_DB_obj  ):
				models.세부_특별평가_DB_V2.objects.get_or_create( 
					특별평가_fk = 특별평가_DB_instance , 
					구분 = 항목.구분,
					성과 = 항목.성과,
					가중치 = 항목.가중치,
					평가점수 = 0
				)
			특별평가_항목_QS = models.세부_특별평가_DB_V2.objects.filter(특별평가_fk = 특별평가_DB_instance)
	특별평가_serializer = serializers.세부_특별평가_DB_Serializer_V2(특별평가_항목_QS, many=True)


	return {'역량평가_api_datas': 역량평가_serializer.data, 
		 '성과평가_api_datas': 성과평가_serializer.data, 
		 '특별평가_api_datas': 특별평가_serializer.data}




class 세부평가_Api_View(APIView):
	""" 
	본인평가 평가체계 , 다른 말로 세부 평가
	"""

	def get(self, request, format=None):
		""" 
		본인평가 평가체계 
		"""
		try:
			#### action 분기 : 해당 method로 return 시킴
			logger.info(f"request.query_params: {request.query_params}")
			action = request.query_params.get('action', 'default_action')
			logger.info(f"action: {action} 실행시작")
			match action:
				case '제출취소':
					return self.제출취소(request)
				case '본인평가':
					#### 평가체계_fk가 없음. 즉,  피평가자 = request.user 로 확인
					try:		
						### 본인평가 instance 찾음				
						평가설정_instance = models.평가설정_DB.objects.get(is_시작=True, is_종료=False)
						평가체계_instance = models.평가체계_DB.objects.get(
							is_참여=True,평가설정_fk=평가설정_instance, 피평가자=request.user, 평가자=request.user, 차수=0 
							)
						data = get_Nested_평가체계_serializer_data( 평가체계_instance=평가체계_instance )
						return Response(data)
					except Exception as e:
						logger.error(f"Error during get_본인평가: {e}")
						logger.error(traceback.format_exc())
						return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})
				case '상급자평가':
					평가체계_fk = request.query_params.get('평가체계_fk', False)
					if not 평가체계_fk:
						return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가체계_fk 가 없습니다.'})
					try:
						평가체계_instance = models.평가체계_DB.objects.get(id=평가체계_fk)
						data = get_Nested_평가체계_serializer_data( 평가체계_instance=평가체계_instance )
						return Response(data)
					except Exception as e:
						logger.error(f"Error during get_평가체계 {평가체계_fk} : {e}")
						logger.error(traceback.format_exc())
						return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})
				case _:
					logger.error(f"세부평가_Api_View 에서 처리할 수 없는 action: {action}")
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'action 이 없습니다.'})
		
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})
	
	@transaction.atomic
	def 제출취소(self, request, *args, **kwargs):
		""" 
		제출취소 
		"""
		try:
			params = request.query_params
			평가체계_fk = params.get('평가체계_fk', False)
			if not 평가체계_fk:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가체계_fk 가 없습니다.'})
			평가체계_instance = models.평가체계_DB.objects.get(id=평가체계_fk)
			평가체계_instance.is_submit = False
			평가체계_instance.save(update_fields=['is_submit'])
			models.역량평가_DB_V2.objects.filter(평가체계_fk=평가체계_instance).update(is_submit=False, 평가점수=0)
			models.성과평가_DB_V2.objects.filter(평가체계_fk=평가체계_instance).update(is_submit=False, 평가점수=0)
			models.특별평가_DB_V2.objects.filter(평가체계_fk=평가체계_instance).update(is_submit=False, 평가점수=0)
			return Response(status=status.HTTP_200_OK, data= self.get_list_data( 평가체계_instance=평가체계_instance ) )
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})

	def save_evaluation_list(self, data_list, model_class, serializer_class, filter_key:str=None):
		if not isinstance(data_list, list):
			data_list = json.loads(data_list)
			if not isinstance(data_list, list):
				raise ValueError("data_list is not a list")
		if not data_list:
			return
		
		saved_results = []
		ids_to_keep = set()
		# 기준값: 특별평가_fk 같은 외래키로 기준 삼아야 함
		기준 = data_list[0]
		filter_kwargs = {}
		if filter_key:
			filter_kwargs = {
				filter_key: 기준.get(filter_key)
			}

		for item in data_list:
			instance = None
			id = item.get('id')
			if isinstance(id, int) and id > 0:
				try:
					instance = model_class.objects.get(id=id)
				except model_class.DoesNotExist:
					instance = None  # fallback to create
			serializer = serializer_class(instance, data=item, partial=True)
			serializer.is_valid(raise_exception=True)
			saved_instance = serializer.save()
			saved_results.append(serializer_class(saved_instance).data)  # serialize saved instance
			ids_to_keep.add(saved_instance.id)

		# 삭제 로직
		if filter_kwargs:
			existing_qs = model_class.objects.filter(**filter_kwargs)
			if ids_to_keep:
				existing_qs = existing_qs.exclude(id__in=ids_to_keep)
			deleted_count, _ = existing_qs.delete()
			logger.info(f"{model_class.__name__} 삭제된 항목 수: {deleted_count}")

		return saved_results
	
	def save_model_개별평가 (self, request ) -> dict:
		역량평가_list =request.data.get('역량평가', [])
		성과평가_list =request.data.get('성과평가', [])
		특별평가_list =request.data.get('특별평가', [])

		역량평가_api_datas = self.save_evaluation_list(역량평가_list, models.세부_역량평가_DB_V2, serializers.세부_역량평가_DB_Serializer_V2)
		성과평가_api_datas = self.save_evaluation_list(성과평가_list, models.세부_성과평가_DB_V2, serializers.세부_성과평가_DB_Serializer_V2, filter_key='성과평가_fk')
		특별평가_api_datas = self.save_evaluation_list(특별평가_list, models.세부_특별평가_DB_V2, serializers.세부_특별평가_DB_Serializer_V2, filter_key='특별평가_fk')

		return {
			'역량평가_api_datas': 역량평가_api_datas, 
			'성과평가_api_datas': 성과평가_api_datas, 
			'특별평가_api_datas': 특별평가_api_datas
		}


	def save_model_개별평가_제출(self, 평가체계_fk:int, model_class, serializer_class, is_제출:bool=False, 평가점수:float=0 ) -> dict:		
		model_class.objects.filter(평가체계_fk_id=평가체계_fk).update(is_submit=is_제출, 평가점수=평가점수)
		return serializer_class(model_class.objects.get(평가체계_fk_id=평가체계_fk), many=False).data

	@transaction.atomic
	def post(self, request, format=None):
		try:
			params = request.query_params
			logger.info(f"params: {params}")
			action = params.get('action', False)
			is_제출 = True if action == '제출' else False

			평가체계_fk = int(params.get('평가체계_fk', False))
			if not action or not 평가체계_fk:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'action 또는 평가체계_fk 가 없습니다.'})
			평가체계_instance = models.평가체계_DB.objects.get(id=평가체계_fk)
			평가설정_instance = 평가체계_instance.평가설정_fk

			logger.info(f"action: {action} 실행시작")
			#### 개별평가 임시 저장
			개별평가_api_datas = self.save_model_개별평가(request)
			#### 개별평가 점수 및  action에 따른 제출여부
			for key, model_class, serializer_class in zip(
				['역량평가_fk', '성과평가_fk', '특별평가_fk'],	
				[models.역량평가_DB_V2, models.성과평가_DB_V2, models.특별평가_DB_V2],
				[serializers.역량평가_DB_Serializer_V2, serializers.성과평가_DB_Serializer_V2, serializers.특별평가_DB_Serializer_V2]
			):
				api_datas:list[dict] = 개별평가_api_datas[f"{key.replace('fk', 'api_datas')}"]
				평가점수 = self.평가점수_계산(key, api_datas)				
				self.save_model_개별평가_제출(
					평가체계_fk, model_class, serializer_class, is_제출=is_제출, 평가점수=평가점수
					)
			#### 평가체계 제출 처리
			models.평가체계_DB.objects.filter(id=평가체계_fk).update(is_submit=is_제출)
			평가체계_instance.refresh_from_db()
			
			if 평가체계_instance.차수 == 0:
				#### get 과 동일한 format 으로 반환
				return Response(status=status.HTTP_200_OK, 
					   data= get_Nested_평가체계_serializer_data( 평가체계_instance=평가체계_instance ) )
			else:
				_dict = get_Nested_평가체계_serializer_data( 평가체계_instance=평가체계_instance )
				_dict['피평가자_본인평가'] = get_Nested_평가체계_serializer_data( 
						models.평가체계_DB.objects.get( 
							평가설정_fk=평가설정_instance,  피평가자= 평가체계_instance.피평가자, 차수=0
						)
					)
				return Response(status=status.HTTP_200_OK, data=_dict)

		
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})

	def 평가점수_계산(self, key:str, api_datas:list[dict]) -> float:
		match key:		
			case '역량평가_fk':
				return sum([ _inst.get('평가점수') for _inst in api_datas ]) / len(api_datas)
			case '성과평가_fk':	
				return sum([ _inst.get('평가점수')*_inst.get('가중치') / 100 for _inst in api_datas ])
			case '특별평가_fk':
				return sum([ _inst.get('평가점수')*_inst.get('가중치')	 / 100 for _inst in api_datas ])
			case _:
				return 0

def get_상급자평가_list_data( 평가자_id:int, 차수:int=None):

	평가설정_instance = models.평가설정_DB.objects.get( is_시작=True, is_종료=False)
	if not 평가설정_instance:
		return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가설정_DB 가 없습니다.'})
	
	평가체계_qs = models.평가체계_DB.objects.filter(
		평가설정_fk = 평가설정_instance, 평가자 = 평가자_id, 차수__gte=1
		).exclude ( 피평가자 = 평가자_id )
	if not 평가체계_qs:
		return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가체계_DB 가 없습니다.'})
	
	map_차수_qs_평가체계 = { 차수: 평가체계_qs.filter(차수=차수) for 차수 in range(1, 평가설정_instance.총평가차수+1) }
	
	map_차수_qs_평가체계_serializer = {}
	for 차수 , qs in map_차수_qs_평가체계.items():
		_list = []
		for inst_평가체계 in qs:
			_dict = get_Nested_평가체계_serializer_data(inst_평가체계 )
			_dict['피평가자_본인평가'] = get_Nested_평가체계_serializer_data( 
				models.평가체계_DB.objects.get( 
					평가설정_fk=평가설정_instance,  피평가자= inst_평가체계.피평가자, 차수=0
				)
			)
			_list.append( _dict )
		map_차수_qs_평가체계_serializer[차수] = _list
	return map_차수_qs_평가체계_serializer

class 상급자평가_Api_View(APIView):
	""" 
	상급자평가 평가체계 , 차수별로 따른 세부 + 종합 평가
	"""

	@transaction.atomic
	def get(self, request, format=None):
		""" 
		상급자평가 평가체계 , 차수별로 따른 세부 + 종합 평가
		"""
		try:
			params = request.query_params
			logger.info(f"params: {params}")
			평가자_id = params.get('평가자_id', False)
			if not 평가자_id:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가자_id 가 없습니다.'})
			차수 = params.get('차수', False)
			# if not 차수:
			# 	return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '차수 가 없습니다.'})
			
			# 평가설정_instance = models.평가설정_DB.objects.get( is_시작=True, is_종료=False)
			# if not 평가설정_instance:
			# 	return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가설정_DB 가 없습니다.'})
			
			# 평가체계_qs = models.평가체계_DB.objects.filter(
			# 	평가설정_fk = 평가설정_instance, 평가자 = 평가자_id, 차수__gte=1
			# 	).exclude ( 피평가자 = 평가자_id )
			# if not 평가체계_qs:
			# 	return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가체계_DB 가 없습니다.'})
			
			# map_차수_qs_평가체계 = { 차수: 평가체계_qs.filter(차수=차수) for 차수 in range(1, 평가설정_instance.총평가차수+1) }
			
			# map_차수_qs_평가체계_serializer = {}
			# for 차수 , qs in map_차수_qs_평가체계.items():
			# 	_list = []
			# 	for inst_평가체계 in qs:
			# 		_dict = get_Nested_평가체계_serializer_data(inst_평가체계 )
			# 		_dict['피평가자_본인평가'] = get_Nested_평가체계_serializer_data( 
			# 			models.평가체계_DB.objects.get( 
			# 				평가설정_fk=평가설정_instance,  피평가자= inst_평가체계.피평가자, 차수=0
			# 			)
			# 		)
			# 		_list.append( _dict )
			# 	map_차수_qs_평가체계_serializer[차수] = _list

			return Response(status=status.HTTP_200_OK, data=get_상급자평가_list_data(평가자_id, 차수))
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})
		

class 상급자평가_BatchUpdate_Api_View(APIView):
	""" 
	상급자평가 평가체계 일괄 저장
	"""

	def save_serializer(self, model_class, serializer_class, data):
		instance = model_class.objects.get(id=data.get('id'))
		serializer = serializer_class(instance, data=data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()

	@transaction.atomic
	def post(self, request):
		"""
		평가체계 제출 처리
		"""
		try:
			datas = request.data  #.get('datas', [])
			if not datas or not isinstance(datas, list):
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'datas 가 없습니다.'})

			평가자_id = None
			차수 = None

			for idx, data in enumerate(datas):
				평가체계_data = data.get('평가체계_data')
				역량평가_data = data.get('역량평가_fk')
				성과평가_data = data.get('성과평가_fk')
				특별평가_data = data.get('특별평가_fk')

				# 필수 값 누락 시 에러 반환
				if not 평가체계_data or not 역량평가_data or not 성과평가_data or not 특별평가_data:
					return Response(
						status=status.HTTP_400_BAD_REQUEST,
						data={'error': f'{idx+1}번째 항목에 필수 데이터 누락됨'}
					)

				평가자_id = 평가체계_data.get('평가자')
				차수 = 평가체계_data.get('차수')

				self.save_serializer(models.평가체계_DB, serializers.평가체계_DB_Serializer, 평가체계_data)
				self.save_serializer(models.역량평가_DB_V2, serializers.역량평가_DB_Serializer_V2, 역량평가_data)
				self.save_serializer(models.성과평가_DB_V2, serializers.성과평가_DB_Serializer_V2, 성과평가_data)
				self.save_serializer(models.특별평가_DB_V2, serializers.특별평가_DB_Serializer_V2, 특별평가_data)

			return Response(status=status.HTTP_200_OK, data=get_상급자평가_list_data(평가자_id, 차수))
		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})


	
	
class 평가결과_종합_API_View(APIView):
	""" 
	평가결과 종합 평가
	"""
	def get(self, request, format=None):
		try:
			평가설정_fk = request.query_params.get('평가설정_fk', False)
			if 평가설정_fk:
				평가설정_instance = models.평가설정_DB.objects.get(id=평가설정_fk)
				logger.info(f'parameter로 받음: 평가설정_instance: {평가설정_instance}')
			else:
				평가설정_instance = models.평가설정_DB.objects.get(is_시작=True, is_종료=False)
			if not 평가설정_instance:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가설정_DB 가 없습니다.'})

			평가체계_QS = models.평가체계_DB.objects.filter(평가설정_fk=평가설정_instance, is_참여=True)
			if not 평가체계_QS:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가결과_DB 가 없습니다.'})
			
			max_차수 = 평가설정_instance.총평가차수
			map_피평가자_to_결과 :dict[str, dict]= {}
			for 차수 in range(max_차수+1):
				for obj in 평가체계_QS.filter(차수=차수):
					피평가자_id = str(obj.피평가자.id)

					if 피평가자_id not in map_피평가자_to_결과:
						map_피평가자_to_결과[피평가자_id] = {}

					map_피평가자_to_결과[피평가자_id][차수] = {
						'평가체계_fk_data' : serializers.평가체계_DB_Serializer(obj, many=False).data,
						'역량평가': serializers.역량평가_DB_Serializer_V2(
							models.역량평가_DB_V2.objects.get(평가체계_fk=obj), many=False
						).data,
						'성과평가': serializers.성과평가_DB_Serializer_V2(
							models.성과평가_DB_V2.objects.get(평가체계_fk=obj), many=False
						).data,
						'특별평가': serializers.특별평가_DB_Serializer_V2(
							models.특별평가_DB_V2.objects.get(평가체계_fk=obj), many=False
						).data,
					}
					### 종합평가 추가
					map_피평가자_to_결과[피평가자_id][차수]['평가체계_fk_data']['종합평가'] = get_종합평가_계산(평가체계_instance=obj)

			for 피평가자_id, 차수_to_결과 in map_피평가자_to_결과.items():
				최종종합평가:list[float] = []
				for 차수, 결과 in 차수_to_결과.items():
					최종종합평가.append( 결과.get('평가체계_fk_data').get('종합평가') * 평가설정_instance.차수별_점유[str(차수)] / 100 )
				map_피평가자_to_결과[피평가자_id]['최종종합평가'] = sum(최종종합평가)

			return Response(status=status.HTTP_200_OK, 
				   data={'평가설정_data': serializers.평가설정_DB_Serializer(평가설정_instance, many=False).data, 
				   		'map_피평가자_to_결과': map_피평가자_to_결과
						})

		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})

