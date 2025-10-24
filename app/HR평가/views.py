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


from . import serializers, models, models_old
# from util.customfilters import *
import util.utils_func as Util
from . import customfilters
from users.models import User, Api_App권한, Api_App권한_User_M2M

import logging, traceback
logger = logging.getLogger('HR평가')

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
		logger.info ( 'get_queryset' )
		return  self.MODEL.objects.order_by('구분','항목','정의')
	
class 평가설정_DB_Copy_Create_API_View ( APIView ):

	def post(self, request, format=None):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if ( id := int( request.data.get('id', False) ) ) and  id > 0 :
				try :
					#### 평가설정 create
					instance_copyd_평가설정 = models.평가설정_DB.objects.get( id = id )
					instance_new_평가설정 = copy.deepcopy( instance_copyd_평가설정 )
					instance_new_평가설정.pk = None
					instance_new_평가설정.시작 = date.today()
					instance_new_평가설정.종료 = date.today()
					instance_new_평가설정.등록자_fk = request.user
					instance_new_평가설정.is_시작 = False
					instance_new_평가설정.is_종료 = False
					instance_new_평가설정.save()

					#### 역량항목_DB create
					qs = models.역량항목_DB.objects.filter( 평가설정_fk= instance_copyd_평가설정 )
					for obj in qs:
						_saved = models.역량항목_DB.objects.create(평가설정_fk=instance_new_평가설정, 구분=obj.구분 )
						for item in obj.item_fks.all():
							_saved.item_fks.add (item)
					## 😀  평가체계_DB 생성오류: Direct assignment to the forward side of a many-to-many set is prohibited. Use item_fks.set() instead.
					# bulk_list = [ models.역량항목_DB(평가설정_fk=instance_new_평가설정, 구분=obj.구분, item_fks=obj.item_fks )  for obj in qs ]
					# models.역량항목_DB.objects.bulk_create( bulk_list )
					#### 평가체계_DB create
					qs = models.평가체계_DB.objects.filter( 평가설정_fk= instance_copyd_평가설정 )
					bulk_list = [ models.평가체계_DB(평가설정_fk=instance_new_평가설정, 평가자=obj.평가자, 피평가자=obj.피평가자, 차수=obj.차수, is_참여=obj.is_참여 )  for obj in qs ]					
					models.평가체계_DB.objects.bulk_create( bulk_list )
					#### 평가체계_DB Append
					userQS = User.objects.filter(is_active = True )
					appendUsers = []
					for user in userQS:
						if qs.filter( 피평가자 = user ).count() != 3:
							appendUsers.append ( user.user_성명 )
							for 차수 in range( instance_new_평가설정.총평가차수 +1 ):
								models.평가체계_DB.objects.create( 평가설정_fk=instance_new_평가설정,  피평가자=user,  평가자 = user if 차수 == 0 else None, 차수=차수)

					return Response ( status=status.HTTP_200_OK, data = { '신규': appendUsers })

				except Exception as e:
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )

		return Response( status=status.HTTP_200_OK, data={'result':'ok'})
	

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
			qs = models.평가체계_DB.objects.filter( 평가설정_fk=instance )
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

		return Response ( status=status.HTTP_200_OK, 
				   data = self.serializer_class(instance_new).data
				   )

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):
		print ( 'create')
		print ( request.data )
		# if isinstance(request.data, QueryDict):  # optional
		# 	request.data._mutable = True
		# 	# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
		# 	# 	ID = request.data.pop('id')
		# 	if not ( 등록자_fk :=request.data.get('등록자_fk', False) ): 
		# 		request.data['등록자_fk'] = request.user.id
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
						models.역량평가_DB.objects.get_or_create( 
							평가체계_fk = 평가체계 , 평가종류=instance.차수별_유형[str(평가체계.차수)]
							)
						####2. 성과평가_DB 생성
						models.성과평가_DB.objects.get_or_create( 
							평가체계_fk = 평가체계 , 평가종류=instance.차수별_유형[str(평가체계.차수)]
							)
						####3. 특별평가_DB 생성
						models.특별평가_DB.objects.get_or_create( 
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
						역량평가_DB_obj = models.역량평가_DB.objects.get( 평가체계_fk = 본인평가 )
						for 항목 in models.역량평가_항목_DB.objects.filter( 평가설정_fk = instance, 차수 = 최대_평가차수 ):
							models.세부_역량평가_DB.objects.get_or_create( 
								역량평가_fk = 역량평가_DB_obj , 
								항목 = 항목
							)

						### 세부_성과평가 항목을 초기 1개만 가져와서 생성함
						성과평가_DB_obj = models.성과평가_DB.objects.get( 평가체계_fk = 본인평가 )
						models.세부_성과평가_DB.objects.get_or_create( 
							성과평가_fk = 성과평가_DB_obj , 
						)
						### 세부_특별평가 항목을 초기 1개만 가져와서 생성함
						특별평가_DB_obj = models.특별평가_DB.objects.get( 평가체계_fk = 본인평가 )
						models.세부_특별평가_DB.objects.get_or_create( 
							특별평가_fk = 특별평가_DB_obj , 
						)
					#### 상급자 평가 : 생성 없음 ===> 본인 평가에 따른 상급자 평가 생성 (평가 체계 및 평가종류에 따라서)
					self._activate_api_app권한( _inst_권한= Api_App권한.objects.get( id = 167 ),  qs평가체계=qs_본인평가 )
					self._activate_api_app권한( _inst_권한= Api_App권한.objects.get( id = 168 ),  qs평가체계=qs_상급자평가 )

			if instance.is_시작 == True and  (is_시작 == 'False'):
				qs평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk = instance )
				with transaction.atomic():
					models.역량평가_DB.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					models.성과평가_DB.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					models.특별평가_DB.objects.filter( 평가체계_fk__평가설정_fk = instance ).delete()
					

					
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
	search_fields =['제목']
	filterset_class =  customfilters.평가체계_DB_Filter


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
		models.역량평가_DB.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)
		models.성과평가_DB.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)
		models.특별평가_DB.objects.filter(평가체계_fk=instance).update(is_submit=False, 평가점수=0)

		역 = models.역량평가_DB.objects.filter(평가체계_fk=instance).first()
		성 = models.성과평가_DB.objects.filter(평가체계_fk=instance).first()
		특 = models.특별평가_DB.objects.filter(평가체계_fk=instance).first()

		if 역:
			models.세부_역량평가_DB.objects.filter(역량평가_fk=역).delete()
		if 성:
			models.세부_성과평가_DB.objects.filter(성과평가_fk=성).delete()
		if 특:
			models.세부_특별평가_DB.objects.filter(특별평가_fk=특).delete()


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


class 평가체계_DB_API_View(APIView):
	""" 평가체계 구축"""

	MODEL = models.평가체계_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가체계_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['제목']

	def post(self, request, format=None):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			from users.models import User
			Users_QS =  User.objects.filter( is_active=True )
			# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
			# 	ID = request.data.pop('id')
			if ( is_생성 := request.data.get('is_생성', False) ) and is_생성 == 'True':
				try :
					평가설정_fk = int (request.data.get('평가설정_fk') )
					models.평가체계_DB.objects.filter( 평가설정_fk = 평가설정_fk).delete()

					총평가차수 = int (request.data.get('총평가차수', -1) )
					from users.models import User
					for user in Users_QS:
						for 차수 in range ( 총평가차수+1 ):
							is_참여= False ### defbuging test 후, True
							models.평가체계_DB.objects.create( 평가설정_fk= models.평가설정_DB.objects.get(pk=평가설정_fk), 피평가자 = user, 평가자 = user if 차수 == 0 else None, 차수=차수, is_참여=is_참여 )
					return Response ( status=status.HTTP_200_OK, data = { 'result': 'ok'})

				except Exception as e:
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )
				
			elif ( is_수정 := request.data.get('is_수정', False) ) and is_수정 == 'True':
				try :
					평가설정_fk = int (request.data.get('평가설정_fk') )
					총평가차수 = int (request.data.get('총평가차수', -1) )

					df = pd.DataFrame(list( self.MODEL.objects.filter( 평가설정_fk=평가설정_fk).values() ))
					df = df.fillna( -1 )
					df = df.replace ( {np.nan: -1})

					df_pivot = (df.pivot_table(index=['피평가자_id'], columns=['차수'], values=['평가자_id']).astype(int) )
					df_reset = df_pivot
					df_reset.columns = df_reset.columns.droplevel()

					api_datas = df_reset.to_dict( orient='records')

					for obj in api_datas:
						obj['is_참여'] = df[(df['차수'] == 0) & (df['피평가자_id'] == obj.get(0) )].iloc[0]['is_참여']
						for 차수 in range (총평가차수+1):
							df_filter = df[(df['차수'] ==차수) & (df['피평가자_id'] == obj.get(0) )]
							차수_id =  int(df_filter.iloc[0]['id'])
							차수_평가자_id = int(df_filter.iloc[0]['평가자_id'])
							차수_평가자_성명 =  Users_QS.get(id=차수_평가자_id).user_성명 if 차수_평가자_id >0 else ''
							# ic ( obj, obj.get(0), '\n', df_filter )

							obj[f"{차수}_id"] = 차수_id 
							obj[f"{차수}_평가자_ID"] = 차수_평가자_id
							obj[f"{차수}_평가자_성명"] = 차수_평가자_성명

					return Response ( status=status.HTTP_200_OK, data = { 'result': api_datas})

				except Exception as e:
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )		

		return Response( status=status.HTTP_200_OK, data={'result':'ok'})


class 평가시스템_구축_API_View(APIView):
	""" 평가체계에서 is_참여=True 에 대해서만 구축"""

	def post(self, request, format=None):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			평가설정_fk = int( request.data.get('평가설정_fk') )
			instance_평가설정 = models.평가설정_DB.objects.get( id = 평가설정_fk)
			if ( is_시작 := request.data.get('is_시작', False) ) and is_시작 == 'True':
				try :
					QS평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk__id =  평가설정_fk ,is_참여=True)

					for 차수 in range( instance_평가설정.총평가차수 +1):
						if 차수 == 0:
							### 본인평가
							for obj in QS평가체계.filter(차수=차수, is_참여=True):
								_instance, _created = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk=obj)
								if not _created:
									_instance.perform_m2m.clear()
									_instance.special_m2m.clear()
									_instance.ability_m2m.clear()
								_instance.perform_m2m.add ( models.성과_평가_DB.objects.create( 평가설정_fk=instance_평가설정, 등록자_fk = obj.평가자))
								_instance.special_m2m.add ( models.특별_평가_DB.objects.create( 평가설정_fk=instance_평가설정, 등록자_fk = obj.평가자))
								final_차수 = self._get_평가자( QS평가체계, obj) 
								구분 = '본인평가' if final_차수 == 0 else f"{str(final_차수)}차평가"
								_inst_역량항목 = models.역량항목_DB.objects.get( 구분=구분, 평가설정_fk__id = 평가설정_fk )								
								for _inst_역량평가사전 in _inst_역량항목.item_fks.all():
									_inst, _isCreated = models.역량_평가_DB.objects.get_or_create( fk = _inst_역량평가사전, 평가설정_fk=instance_평가설정, 등록자_fk=obj.평가자)
									_instance.ability_m2m.add ( _inst )
						else:
							match instance_평가설정.차수별_유형.get(str(차수)):	### json field : '개별' or '종합'
								case '개별':
									for obj in QS평가체계.filter(차수=차수,피평가자__isnull=False).distinct():
										_instance, _isCreated = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk=QS평가체계.get( 차수=0, 피평가자=obj.피평가자))

								case '종합':
									for obj in QS평가체계.filter(차수=차수, 피평가자__isnull=False).distinct():
										_instance,_isCreated = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk= QS평가체계.get( 차수=0, 피평가자=obj.피평가자))
					
					return Response ( status=status.HTTP_200_OK, data = { 'result': 'ok'})

				except Exception as e:
					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )

	def _get_평가자 (self, QS평가체계, obj) ->int:
		차수list = list( set([ _inst.차수    for _inst in QS평가체계.filter( 평가자 = obj.평가자) ]) )
		차수list.sort()
		return 차수list[-1]


# class 역량평가_항목_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.역량평가_항목_DB_V2
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.역량평가_항목_DB_Serializer_V2
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가설정_fk']
# 	# filterset_class =  customfilters.역량평가_항목_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	
# 	def list(self, request, *args, **kwargs):
# 		params = request.query_params
# 		logger.info ( params )
# 		평가설정_fk = params.get('평가설정_fk')
# 		평가설정_instance = models.평가설정_DB.objects.get( id = 평가설정_fk )
# 		총평가차수 = 평가설정_instance.총평가차수
# 		if not 평가설정_fk:
# 			return Response({"error": "평가설정_fk is required"}, status=400)

# 		# 기존 DB 항목 조회
# 		existing_items = self.MODEL.objects.filter(
# 			평가설정_fk_id=평가설정_fk,
# 			차수__in=range(총평가차수+1)
# 		)
# 		logger.info(f"Existing items: {existing_items}")
# 		logger.info(f"Existing items: {existing_items.count()}")
# 		existing_map = {
# 			f"{item.차수}_{item.항목.id}": item for item in existing_items if item.항목 is not None
# 		}
# 		logger.info(f"Existing map: {existing_map}")
# 		# 사전 전체 항목 기준으로 출력
# 		전체_역량평가사전항목 = models.역량평가사전_DB.objects.all()
# 		result_data = []

# 		for 차수 in range(총평가차수+1):
# 			for 항목_instance in 전체_역량평가사전항목:
# 				key = f"{차수}_{항목_instance.id}"
# 				if key in existing_map:
# 					# 이미 저장된 항목은 serializer로
# 					serialized = self.serializer_class(existing_map[key]).data
# 				else:
# 					# 없는 항목은 기본값으로 구성
# 					serialized = {
# 							"id": -1,
# 							"평가설정_fk": 평가설정_fk,
# 							"차수": 차수,
# 							"항목": 항목_instance.id,
# 							"항목_이름": 항목_instance.항목,
# 							"구분": 항목_instance.구분,
# 							"정의": 항목_instance.정의
# 						}
# 				result_data.append(serialized)
# 		result_data.sort(key=lambda x: (x['차수'], x['구분'], x['항목_이름']))

# 		return Response(result_data)
		
# 	@action(detail=False, methods=['post'], url_path='bulk')
# 	def bulk(self, request, *args, **kwargs):
# 		logger.info(f"Request data: {request.data}")
# 		_list = json.loads(request.data.get('_list', []))
# 		평가설정_fk = request.data.get('평가설정_fk', False)
# 		if not isinstance(_list, list) or not 평가설정_fk:
# 			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'No data provided'})
		
# 		valid_ids = set()
# 		try:
# 			with transaction.atomic():
# 				for _inst in _list:
# 					if _inst.get('id') == -1:
# 						created =models.역량평가_항목_DB_V2.objects.create( 
# 							평가설정_fk_id = 평가설정_fk, 차수 = _inst.get('차수'), 항목_id = _inst.get('항목') 
# 							)
# 						valid_ids.add(created.id)
# 					else:
# 						models.역량평가_항목_DB_V2.objects.filter( id = _inst.get('id') ).update( 
# 							평가설정_fk_id = 평가설정_fk, 차수 = _inst.get('차수'), 항목_id = _inst.get('항목') 
# 							)
# 						valid_ids.add(_inst.get('id'))

# 				### 삭제 : valid_ids 에 없는 항목 삭제 , 만약 empty 라면 .exclude(id__in=[]) → 전체 항목을 포함 (즉, 아무 id도 제외되지 않음)
# 				models.역량평가_항목_DB_V2.objects.filter(평가설정_fk_id=평가설정_fk).exclude(id__in=valid_ids).delete()

# 			return Response(status=status.HTTP_200_OK, data={'result': 'ok'})
# 		except Exception as e:
# 			logger.error(f"Error during bulk update: {e}")
# 			logger.error(traceback.format_exc())
# 			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})

class 역량항목_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.역량항목_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.역량항목_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가설정_fk']
	filterset_class =  customfilters.역량항목_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):
		# if isinstance(request.data, QueryDict):  # optional
		# 	request.data._mutable = True
		# 	# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
		# 	# 	ID = request.data.pop('id')
		# 	if not ( 등록자_fk :=request.data.get('등록자_fk', False) ): 
		# 		request.data['등록자_fk'] = request.user.id
		return super().create(request, *args, **kwargs )

class 평가결과_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.평가결과_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가결과_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.평가결과_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')

#### 5-28 신규 
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
			
		result['평가체계_data'].update( get_종합평가_계산(평가체계_instance) )
		logger.info(f"result['평가체계_data']: {result['평가체계_data']}")
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
	
	역량평가_DB_instance = models.역량평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	성과평가_DB_instance = models.성과평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	특별평가_DB_instance = models.특별평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	종합평가 = 역량평가_DB_instance.평가점수 * 점유_역량 / 100 + 성과평가_DB_instance.평가점수 * 점유_성과 / 100 + 특별평가_DB_instance.평가점수 * 점유_특별 / 100
	return {'종합평가': 종합평가}
	
	
		
def get_3대평가_serializer_data(평가체계_instance:models.평가체계_DB, 평가유형:str, 차수:int):
	역량평가_DB_instance = models.역량평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	성과평가_DB_instance = models.성과평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
	특별평가_DB_instance = models.특별평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)

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
	역량평가_DB_instance = models.역량평가_DB_V2.objects.get(평가체계_fk = 평가체계_instance)
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

class 상급자평가_Api_View(APIView):
	""" 
	상급자평가 평가체계 , 차수별로 따른 세부 + 종합 평가
	"""
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

			return Response(status=status.HTTP_200_OK, data=map_차수_qs_평가체계_serializer)
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
			else:
				평가설정_instance = models.평가설정_DB.objects.get(is_시작=True, is_종료=False)
			if not 평가설정_instance:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가설정_DB 가 없습니다.'})

			평가체계_QS = models.평가체계_DB.objects.filter(평가설정_fk=평가설정_instance, is_참여=True)
			if not 평가체계_QS:
				return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': '평가결과_DB 가 없습니다.'})
			
			max_차수 = 평가설정_instance.총평가차수
			map_피평가자_to_결과 :dict[str, dict]= {}
			for 차수 in range(max_차수):
				for obj in 평가체계_QS.filter(차수=차수):
					피평가자_id = str(obj.피평가자.id)

					if 피평가자_id not in map_피평가자_to_결과:
						map_피평가자_to_결과[피평가자_id] = {}

					map_피평가자_to_결과[피평가자_id][차수] = {
						'평가체계_fk_data' : serializers.평가체계_DB_Serializer(obj, many=False).data,
						'역량평가': serializers.역량평가_DB_Serializer(
							models.역량평가_DB.objects.get(평가체계_fk=obj), many=False
						).data,
						'성과평가': serializers.성과평가_DB_Serializer(
							models.성과평가_DB.objects.get(평가체계_fk=obj), many=False
						).data,
						'특별평가': serializers.특별평가_DB_Serializer(
							models.특별평가_DB.objects.get(평가체계_fk=obj), many=False
						).data,
					}


			# logger.info(f"map_피평가자_to_결과 : {map_피평가자_to_결과}")

			return Response(status=status.HTTP_200_OK, 
				   data={'평가설정_data': serializers.평가설정_DB_Serializer(평가설정_instance, many=False).data, 
				   		'map_피평가자_to_결과': map_피평가자_to_결과
						})

		except Exception as e:
			logger.error(f"Error during bulk update: {e}")
			logger.error(traceback.format_exc())
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})




class 본인평가_DB_ViewSet(viewsets.ModelViewSet):

	MODEL = models.평가결과_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가결과_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.평가결과_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수=0).order_by('-id')
	
	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if ( is_submit :=request.data.get('is_submit', False) ) and is_submit == 'True': 
				instance = self.get_object()
				# 평가점수s = [ _inst.평가점수 for _inst in instance.ability_m2m.all() ]
				# instance.역량점수 =  round( sum(평가점수s)/len(평가점수s), 2)
				# instance.성과점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in instance.perform_m2m.all() ] )
				# instance.특별점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in instance.special_m2m.all() ] )
				# instance.save()

				QS_상급평가 = models.평가결과_DB.objects.exclude(id=instance.id).filter( 피평가자_평가체계_fk = instance.평가체계_fk )	
				if QS_상급평가:
					for _inst in QS_상급평가:
						try:
							_inst.ability_m2m.clear()
							_inst.perform_m2m.clear()
							_inst.special_m2m.celar()
						except Exception as e:
							pass
						for m2m in instance.ability_m2m.all():
							_inst.ability_m2m.add (self.__m2m_save(m2m, _inst ))
						for m2m in instance.perform_m2m.all():
							_inst.perform_m2m.add (self.__m2m_save(m2m, _inst ))
						for m2m in instance.special_m2m.all():
							_inst.special_m2m.add (self.__m2m_save(m2m, _inst ))


		return super().update(request, *args, **kwargs )
	
	def __m2m_save(self, m2m, _inst):
		
		m2m.id = None
		m2m.평가점수 = 0
		m2m.등록자_fk = _inst.평가체계_fk.평가자
		m2m.save()
		return m2m


class 상급자평가_DB_ViewSet(viewsets.ModelViewSet):

	MODEL = models.평가결과_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가결과_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.평가결과_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수__gte=1).order_by('-id')
	

class 상급자평가_DB_API_View(APIView):
	MODEL = models.평가결과_DB

	def post(self, request, fromat=None ):
		평가설정_instance = models.평가설정_DB.objects.get(is_종료=False)
		QS = self.MODEL.objects.exclude(평가체계_fk__피평가자 = self.request.user).filter(평가체계_fk__평가설정_fk= 평가설정_instance ).filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수__gte=1).order_by('-id')
		차수별_대상자_dict = { 차수: self._get_IDs( QS.filter( 평가체계_fk__차수= 차수) ) for 차수  in range (1, 평가설정_instance.총평가차수+1) }
		차수별_is_submit = {  차수: self._get_is_submit( QS.filter( 평가체계_fk__차수= 차수) ) for 차수  in range (1, 평가설정_instance.총평가차수+1) }

		return Response ( status=status.HTTP_200_OK, data={'차수별_대상자' : 차수별_대상자_dict ,'차수별_유형': 평가설정_instance.차수별_유형, '차수별_is_submit': 차수별_is_submit })

	def _get_IDs (self, QS) -> list[int]:		
		return [ obj.id for obj in QS ]
	def _get_is_submit (self, QS) -> list[bool]:		
		return [ obj.is_submit for obj in QS ]

class 역량_평가_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.역량_평가_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.역량_평가_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.역량_평가_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('fk__구분','fk__항목')
		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('fk__구분','fk__항목')
	def create(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['등록자_fk'] = request.user.id
			request.data['등록자'] = datetime.now()
		return super().create( request, *args, **kwargs )

	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['등록자_fk'] = request.user.id
			request.data['등록자'] = datetime.now()
		return super().update( request, *args, **kwargs )

class 성과_평가_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.성과_평가_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.성과_평가_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.성과_평가_DB_Filter

	def get_queryset(self):		
		return  self.MODEL.objects.order_by('-id')
		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('-id')
	
class 특별_평가_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.특별_평가_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.특별_평가_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['평가체계_fk']
	filterset_class =  customfilters.특별_평가_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('-id')


class Check_평가점수_API_View(APIView):
	MODEL = models.평가결과_DB

	def post(self, request, fromat=None ):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			ID = int( request.data.get('id') )
			instance_평가결과 = models.평가결과_DB.objects.get( id = ID)

			역량check = self._check_역량 ( instance_평가결과.ability_m2m )
			성과check = self._check_성과_특별(instance_평가결과.perform_m2m )
			특별check = self._check_성과_특별(instance_평가결과.special_m2m )

			return Response(status=status.HTTP_200_OK,
				data= {'역량check':역량check, '성과check':성과check, '특별check':특별check })
	
	def _check_역량(self, ability_m2m) -> dict:		
		평가점수s = [ instance.평가점수 for instance in ability_m2m.all() ]
		return {'항목수': len( 평가점수s), '평가점수': round( sum(평가점수s)/len(평가점수s), 2)}

	def _check_성과_특별(self, m2m) -> dict:
		평가점수s = [ instance.평가점수*instance.가중치 / 100 for instance in m2m.all() ]
		가중치s =  [ instance.가중치 for instance in m2m.all() ]

		return {'가중치' : sum(가중치s),  '항목수': len( 평가점수s), '평가점수': round( sum(평가점수s), 2)  }
	
class 종합평가_결과_API_View(APIView):
	
	def post(self, request, fromat=None ):
		if isinstance(request.data, QueryDict):  # optional
		
			request.data._mutable = True
			퍙기설정_FK = int( request.data.get('평가설정_fk') )
			평가설정_Instance = models.평가설정_DB.objects.get( id = 퍙기설정_FK )

			df = pd.DataFrame(list( models.평가체계_DB.objects.filter( 평가설정_fk=평가설정_Instance, is_참여=True ).values() ))
			df = df.fillna( -1 )
			df = df.replace ( {np.nan: -1})

			df_pivot = (df.pivot_table(index=['피평가자_id'], columns=['차수'], values=['평가자_id']).astype(int) )

			df_reset = df_pivot
			df_reset.columns = df_reset.columns.droplevel()

			api_datas = df_reset.to_dict( orient='records')
			Users_QS =  User.objects.filter( is_active=True )
			##😀 api_datas : 평가체게에 대해
			QS_평가결과 = models.평가결과_DB.objects.filter ( 평가체계_fk__평가설정_fk = 평가설정_Instance)

			for obj in api_datas:
				for 차수 in range (평가설정_Instance.총평가차수+1):
					df_filter = df[(df['차수'] ==차수) & (df['피평가자_id'] == obj.get(0) )]
					차수_id =  int(df_filter.iloc[0]['id'])
					차수_평가자_id = int(df_filter.iloc[0]['평가자_id'])
					차수_평가자_성명 =  Users_QS.get(id=차수_평가자_id).user_성명 if 차수_평가자_id >0 else ''
					# ic ( obj, obj.get(0), '\n', df_filter )
					obj[f"{차수}_id"] = 차수_id 
					obj[f"{차수}_평가자_ID"] = 차수_평가자_id
					obj[f"{차수}_평가자_성명"] = 차수_평가자_성명

					_inst_평가결과 = QS_평가결과.get( 평가체계_fk_id = 차수_id)

					for name in ['id','is_submit', '역량점수','성과점수','특별점수','종합점수'] :						
						obj[f"{차수}_{name if name !='id' else '평가결과_id'}"] = getattr ( _inst_평가결과, name )

			차수별_점유:dict = 평가설정_Instance.차수별_점유
			for obj in api_datas:
				keyList = list ( obj.keys() )
				역량점수s = [ obj.get(name) for name in keyList if '역량점수' in str(name) ]
				성과점수s = [ obj.get(name) for name in keyList if '성과점수' in str(name) ]
				특별점수s = [ obj.get(name) for name in keyList if '특별점수' in str(name) ]
				종합점수s = [ obj.get(name) for name in keyList if '종합점수' in str(name) ]

				obj['최종_역량'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(역량점수s) ] )
				obj['최종_성과'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(성과점수s) ] )
				obj['최종_특별'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(특별점수s) ] )
				obj['최종_종합'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(종합점수s) ] )

			return Response(status=status.HTTP_200_OK, data=api_datas )
	

class 평가설정DB_Old_ViewSet(viewsets.ModelViewSet):
	MODEL =  models_old.평가설정DB_Old
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.평가설정DB_Old_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['평가체계_fk']
	# filterset_class =  customfilters.종합평가_결과_Old_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 종합평가_결과_Old_ViewSet(viewsets.ModelViewSet):
	MODEL =  models_old.종합평가_결과_Old
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.종합평가_결과_Old_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['평가체계_fk']
	filterset_class =  customfilters.종합평가_결과_Old_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class HR평가_API_View(APIView):

	def get(self, request, fromat=None ):
		params = request.query_params
		user = request.user
		평가설정_fk = params.get('평가설정_fk')
		평가설정_instance = models.평가설정_DB.objects.get( id = 평가설정_fk )

		평가체계_qs = models.평가체계_DB.objects.filter( 
			평가설정_fk = 평가설정_instance, is_참여=True )
		
		본인평가_평가체계_instance = 평가체계_qs.get( 차수 = 0 )
		
		본인평가_역량평가_instance = models.역량평가_DB.objects.get( 
			평가체계_fk = 본인평가_평가체계_instance )
		
		본인평가_역량평가_항목_qs = models.역량평가_항목_DB.objects.filter( 
			역량평가_fk = 본인평가_역량평가_instance )
		
		본인평가_성과평가_instance = models.성과평가_DB.objects.get( 
			평가체계_fk = 본인평가_평가체계_instance )
		
		본인평가_성과평가_항목_qs = models.세부_성과평가_DB.objects.filter( 
			성과평가_fk = 본인평가_성과평가_instance )	
		
		본인평가_특별평가_instance = models.특별평가_DB.objects.get( 
			평가체계_fk = 본인평가_평가체계_instance )
		
		본인평가_특별평가_항목_qs = models.세부_특별평가_DB.objects.filter( 
			특별평가_fk = 본인평가_특별평가_instance )
		
		if not 본인평가_역량평가_항목_qs.count()  :
			항목_all = models.역량평가_항목_DB.objects.filter(	
				평가설정_fk = 평가설정_instance, 차수 = 0
			).all()
			for 항목 in 항목_all :
				models.세부_역량평가_DB.objects.create(
					역량평가_fk = 본인평가_역량평가_instance,
					항목 = 항목
				)
		세부_역량평가_datas = serializers.세부_역량평가_DB_Serializer(
			models.세부_역량평가_DB.objects.filter(
				역량평가_fk = 본인평가_역량평가_instance
			).all(), many=True
		).data

		return Response(status=status.HTTP_200_OK, data=세부_역량평가_datas)
	

