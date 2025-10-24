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
from django.db.models import Count, Sum , functions, Q, QuerySet

import os
import json
import copy
import pandas as pd
import numpy as np

# ic.disable()

from . import serializers, models, customfilters
# from util.customfilters import *
import util.utils_func as Util
from users.models import User, Api_App권한

class 차량관리_차량번호_사용자_API_View ( APIView):	
	def get(self, request, format=None):
		q_filters =  Q( write_users_m2m__in = [request.user]) | Q( admin_users_m2m__in = [request.user] )
		차량번호 = set(list(models.차량관리_기준정보.objects.filter( q_filters). values_list('차량번호', flat=True)))
		ic ( 차량번호 )
		return Response ( 차량번호 )

class 차량관리_기준정보_ViewSet(viewsets.ModelViewSet):
	MODEL = models.차량관리_기준정보
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.차량관리_기준정보_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['차량번호','차종']
	# filterset_class =  역량평가사전_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):
		ic ( request.data )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			# request.data['user_fk'] = self.request.user.id 
			if request.data.get('등록자_fk', None) :  request.data.pop('등록자_fk')
		ic ( request.data )
		return super().create(request, *args, **kwargs )
	
class 차량관리_운행DB_관리자_ViewSet(viewsets.ModelViewSet):
	MODEL = models.차량관리_운행DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.차량관리_운행DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['차량번호_fk__차량번호','정비사항','비고','관련근거']
	# filterset_class =  역량평가사전_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
class 차량관리_운행DB_사용자_ViewSet(차량관리_운행DB_관리자_ViewSet):

	def get_queryset(self):
		user = self.request.user
		ic ( user )
		q_filters =  Q( 차량번호_fk__write_users_m2m__in = [user] ) | Q( 차량번호_fk__admin_users_m2m__in = [user] )
		ic ( q_filters )
		return  self.MODEL.objects.filter( q_filters).order_by('-id').distinct()
	
	def create(self, request, *args, **kwargs):
		ic ( request.data )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			# request.data['user_fk'] = self.request.user.id 
			if request.data.get('차량번호', None) :  
				차량번호str = request.data.pop('차량번호')
				ic (차량번호str, type(차량번호str))
				try:
					request.data['차량번호_fk'] = models.차량관리_기준정보.objects.filter(차량번호__in=차량번호str)[0].id
				except Exception as e:
					ic ( f" error : {str(e)}")
		ic ( request.data )
		return super().create(request, *args, **kwargs )
	
# class 평가설정_DB_Copy_Create_API_View ( APIView ):

# 	def post(self, request, format=None):
# 		ic ( request.data )
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			if ( id := int( request.data.get('id', False) ) ) and  id > 0 :
# 				try :
# 					#### 평가설정 create
# 					instance_copyd_평가설정 = models.평가설정_DB.objects.get( id = id )
# 					instance_new_평가설정 = copy.deepcopy( instance_copyd_평가설정 )
# 					instance_new_평가설정.pk = None
# 					instance_new_평가설정.시작 = date.today()
# 					instance_new_평가설정.종료 = date.today()
# 					instance_new_평가설정.등록자_fk = request.user
# 					instance_new_평가설정.is_시작 = False
# 					instance_new_평가설정.is_종료 = False
# 					instance_new_평가설정.save()

# 					#### 역량항목_DB create
# 					qs = models.역량항목_DB.objects.filter( 평가설정_fk= instance_copyd_평가설정 )
# 					for obj in qs:
# 						_saved = models.역량항목_DB.objects.create(평가설정_fk=instance_new_평가설정, 구분=obj.구분 )
# 						for item in obj.item_fks.all():
# 							_saved.item_fks.add (item)
# 					## 😀  평가체계_DB 생성오류: Direct assignment to the forward side of a many-to-many set is prohibited. Use item_fks.set() instead.
# 					# bulk_list = [ models.역량항목_DB(평가설정_fk=instance_new_평가설정, 구분=obj.구분, item_fks=obj.item_fks )  for obj in qs ]
# 					# models.역량항목_DB.objects.bulk_create( bulk_list )
# 					#### 평가체계_DB create
# 					qs = models.평가체계_DB.objects.filter( 평가설정_fk= instance_copyd_평가설정 )
# 					bulk_list = [ models.평가체계_DB(평가설정_fk=instance_new_평가설정, 평가자=obj.평가자, 피평가자=obj.피평가자, 차수=obj.차수, is_참여=obj.is_참여 )  for obj in qs ]					
# 					models.평가체계_DB.objects.bulk_create( bulk_list )
# 					#### 평가체계_DB Append
# 					userQS = User.objects.filter(is_active = True )
# 					appendUsers = []
# 					for user in userQS:
# 						if qs.filter( 피평가자 = user ).count() != 3:
# 							appendUsers.append ( user.user_성명 )
# 							for 차수 in range( instance_new_평가설정.총평가차수 +1 ):
# 								models.평가체계_DB.objects.create( 평가설정_fk=instance_new_평가설정,  피평가자=user,  평가자 = user if 차수 == 0 else None, 차수=차수)

# 					return Response ( status=status.HTTP_200_OK, data = { '신규': appendUsers })

# 				except Exception as e:
# 					ic ( '평가체계_DB 생성오류:', e)
# 					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )

# 		return Response( status=status.HTTP_200_OK, data={'result':'ok'})
	

# class 평가설정_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.평가설정_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가설정_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['제목']
# 	# filterset_class =  평가설정_DB_Filter


# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	
# 	def create(self, request, *args, **kwargs):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
# 			# 	ID = request.data.pop('id')
# 			if not ( 등록자_fk :=request.data.get('등록자_fk', False) ): 
# 				request.data['등록자_fk'] = request.user.id
# 		return super().create(request, *args, **kwargs )

# 	def update(self, request, *args, **kwargs):
# 		instance = self.get_object()
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
# 			# 	ID = request.data.pop('id')
# 			if ( 차수별_점유 :=request.data.get('차수별_점유', False) ): 
# 				ic ( 차수별_점유, type(차수별_점유),  json.dumps( 차수별_점유, ensure_ascii=False) )
# 				# request.data['차수별_점유'] = json.dumps( 차수별_점유, ensure_ascii=False)
# 			if ( is_시작 :=request.data.get('is_시작', False) ) and is_시작 == 'True': 
# 				qs본인평가 = models.평가체계_DB.objects.filter( 평가설정_fk = instance , 차수=0, is_참여=True)
# 				self._activate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 167 ),
# 											qs = qs본인평가 )

# 				qs상급자평가 = models.평가체계_DB.objects.filter( 평가설정_fk = instance , 차수__gte=1, is_참여=True)
# 				self._activate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 168 ),
# 							qs = qs상급자평가 )
			
# 			elif ( is_종료 :=request.data.get('is_종료', False) ) and is_종료 == 'True': 
# 				self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 167 ) )
# 				self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 168 ) )

# 		return super().update(request, *args, **kwargs )
	
# 	def _activate_api_app권한(self, _inst_권한:Api_App권한,  qs:QuerySet[models.평가체계_DB]  ):
# 		_inst_권한.user_pks.clear()
# 		for _inst in qs:
# 			if bool( _inst.평가자) :
# 				_inst_권한.user_pks.add ( _inst.평가자)
# 		_inst_권한.is_Run = True
# 		_inst_권한.save( update_fields=['is_Run'])

# 	def _deactivate_api_app권한(self, _inst_권한:Api_App권한 ):
# 		_inst_권한.user_pks.clear()
# 		_inst_권한.is_Run = False
# 		_inst_권한.save( update_fields=['is_Run'])

# 	def destroy(self, request, *args, **kwargs):
# 		self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 167 ) )
# 		self._deactivate_api_app권한 ( _inst_권한= Api_App권한.objects.get( id = 168 ) )
		
# 		return super().destroy(request, *args, **kwargs)


# class 평가체계_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.평가체계_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가체계_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['제목']
# 	filterset_class =  customfilters.평가체계_DB_Filter


# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	
# 	def update(self, request, *args, **kwargs):
# 		ic ( request.data )
# 		instance : models.평가체계_DB = self.get_object()
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			if (is_참여 :=request.data.get('is_참여', False) ): 

# 				for 상급평가_instance in models.평가체계_DB.objects.filter( 평가설정_fk = instance.평가설정_fk, 피평가자 = instance.평가자, 차수__gte=1 ):
# 					상급평가_instance.is_참여 = is_참여
# 					ic( 상급평가_instance, is_참여)
# 					상급평가_instance.save(update_fields=['is_참여'])
		
# 		return super().update(request, *args, **kwargs )
	
# 	def list(self, request, *args, **kwargs):
# 		queryset = self.filter_queryset(self.get_queryset())

# 		page = self.paginate_queryset(queryset)
# 		if page is not None:
# 			serializer = self.get_serializer(page, many=True)
# 			return self.get_paginated_response(serializer.data)

# 		serializer = self.get_serializer(queryset, many=True)
# 		return Response(serializer.data)


# class 평가체계_DB_API_View(APIView):
# 	""" 평가체계 구축"""

# 	MODEL = models.평가체계_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가체계_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['제목']

# 	def post(self, request, format=None):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			from users.models import User
# 			Users_QS =  User.objects.filter( is_active=True )
# 			# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
# 			# 	ID = request.data.pop('id')
# 			if ( is_생성 := request.data.get('is_생성', False) ) and is_생성 == 'True':
# 				try :
# 					평가설정_fk = int (request.data.get('평가설정_fk') )
# 					models.평가체계_DB.objects.filter( 평가설정_fk = 평가설정_fk).delete()

# 					총평가차수 = int (request.data.get('총평가차수', -1) )
# 					from users.models import User
# 					for user in Users_QS:
# 						for 차수 in range ( 총평가차수+1 ):
# 							is_참여= False ### defbuging test 후, True
# 							models.평가체계_DB.objects.create( 평가설정_fk= models.평가설정_DB.objects.get(pk=평가설정_fk), 피평가자 = user, 평가자 = user if 차수 == 0 else None, 차수=차수, is_참여=is_참여 )
# 					return Response ( status=status.HTTP_200_OK, data = { 'result': 'ok'})

# 				except Exception as e:
# 					ic ( '평가체계_DB 생성오류:', e)
# 					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )
				
# 			elif ( is_수정 := request.data.get('is_수정', False) ) and is_수정 == 'True':
# 				try :
# 					평가설정_fk = int (request.data.get('평가설정_fk') )
# 					총평가차수 = int (request.data.get('총평가차수', -1) )

# 					df = pd.DataFrame(list( self.MODEL.objects.filter( 평가설정_fk=평가설정_fk).values() ))
# 					df = df.fillna( -1 )
# 					df = df.replace ( {np.nan: -1})
# 					ic ( 'df \n', df)

# 					df_pivot = (df.pivot_table(index=['피평가자_id'], columns=['차수'], values=['평가자_id']).astype(int) )
# 					ic ( df_pivot )
# 					df_reset = df_pivot
# 					df_reset.columns = df_reset.columns.droplevel()

# 					api_datas = df_reset.to_dict( orient='records')
# 					ic ( api_datas, '\n\n' )

# 					for obj in api_datas:
# 						obj['is_참여'] = df[(df['차수'] == 0) & (df['피평가자_id'] == obj.get(0) )].iloc[0]['is_참여']
# 						for 차수 in range (총평가차수+1):
# 							df_filter = df[(df['차수'] ==차수) & (df['피평가자_id'] == obj.get(0) )]
# 							차수_id =  int(df_filter.iloc[0]['id'])
# 							차수_평가자_id = int(df_filter.iloc[0]['평가자_id'])
# 							차수_평가자_성명 =  Users_QS.get(id=차수_평가자_id).user_성명 if 차수_평가자_id >0 else ''
# 							# ic ( obj, obj.get(0), '\n', df_filter )

# 							obj[f"{차수}_id"] = 차수_id 
# 							obj[f"{차수}_평가자_ID"] = 차수_평가자_id
# 							obj[f"{차수}_평가자_성명"] = 차수_평가자_성명

# 					ic ( api_datas , '\n\n')
# 					return Response ( status=status.HTTP_200_OK, data = { 'result': api_datas})

# 				except Exception as e:
# 					ic ( '평가체계_DB 수정오류:', e)
# 					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )		

# 		return Response( status=status.HTTP_200_OK, data={'result':'ok'})


# class 평가시스템_구축_API_View(APIView):
# 	""" 평가체계에서 is_참여=True 에 대해서만 구축"""

# 	def post(self, request, format=None):
# 		ic ( request.data )
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			평가설정_fk = int( request.data.get('평가설정_fk') )
# 			instance_평가설정 = models.평가설정_DB.objects.get( id = 평가설정_fk)
# 			if ( is_시작 := request.data.get('is_시작', False) ) and is_시작 == 'True':
# 				try :
# 					QS평가체계 = models.평가체계_DB.objects.filter( 평가설정_fk__id =  평가설정_fk ,is_참여=True)
# 					ic ( QS평가체계, QS평가체계.count() )

# 					for 차수 in range( instance_평가설정.총평가차수 +1):
# 						if 차수 == 0:
# 							### 본인평가
# 							for obj in QS평가체계.filter(차수=차수, is_참여=True):
# 								_instance, _created = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk=obj)
# 								if not _created:
# 									_instance.perform_m2m.clear()
# 									_instance.special_m2m.clear()
# 									_instance.ability_m2m.clear()
# 								_instance.perform_m2m.add ( models.성과_평가_DB.objects.create( 평가설정_fk=instance_평가설정, 등록자_fk = obj.평가자))
# 								_instance.special_m2m.add ( models.특별_평가_DB.objects.create( 평가설정_fk=instance_평가설정, 등록자_fk = obj.평가자))
# 								final_차수 = self._get_평가자( QS평가체계, obj) 
# 								구분 = '본인평가' if final_차수 == 0 else f"{str(final_차수)}차평가"
# 								_inst_역량항목 = models.역량항목_DB.objects.get( 구분=구분, 평가설정_fk__id = 평가설정_fk )								
# 								for _inst_역량평가사전 in _inst_역량항목.item_fks.all():
# 									_inst, _isCreated = models.역량_평가_DB.objects.get_or_create( fk = _inst_역량평가사전, 평가설정_fk=instance_평가설정, 등록자_fk=obj.평가자)
# 									_instance.ability_m2m.add ( _inst )
# 						else:
# 							match instance_평가설정.차수별_유형.get(str(차수)):	### json field : '개별' or '종합'
# 								case '개별':
# 									for obj in QS평가체계.filter(차수=차수,피평가자__isnull=False).distinct():
# 										_instance, _isCreated = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk=QS평가체계.get( 차수=0, 피평가자=obj.피평가자))

# 								case '종합':
# 									for obj in QS평가체계.filter(차수=차수, 피평가자__isnull=False).distinct():
# 										_instance,_isCreated = models.평가결과_DB.objects.get_or_create( 평가체계_fk=obj, 피평가자_평가체계_fk= QS평가체계.get( 차수=0, 피평가자=obj.피평가자))
					
# 					return Response ( status=status.HTTP_200_OK, data = { 'result': 'ok'})

# 				except Exception as e:
# 					ic ( '평가시스템_구축_API_View:', e)
# 					return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': str(e)} )

# 	def _get_평가자 (self, QS평가체계, obj) ->int:
# 		차수list = list( set([ _inst.차수    for _inst in QS평가체계.filter( 평가자 = obj.평가자) ]) )
# 		차수list.sort()
# 		return 차수list[-1]


# class 역량항목_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.역량항목_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.역량항목_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가설정_fk']
# 	filterset_class =  customfilters.역량항목_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	
# 	def create(self, request, *args, **kwargs):
# 		ic ( request.data )
# 		# if isinstance(request.data, QueryDict):  # optional
# 		# 	request.data._mutable = True
# 		# 	# if not ( ID:= request.data.get('id', False) ) or ID == '-1':
# 		# 	# 	ID = request.data.pop('id')
# 		# 	if not ( 등록자_fk :=request.data.get('등록자_fk', False) ): 
# 		# 		request.data['등록자_fk'] = request.user.id
# 		return super().create(request, *args, **kwargs )

# class 평가결과_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.평가결과_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가결과_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.평가결과_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')


# class 본인평가_DB_ViewSet(viewsets.ModelViewSet):

# 	MODEL = models.평가결과_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가결과_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.평가결과_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수=0).order_by('-id')
	
# 	def update(self, request, *args, **kwargs):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			ic ( request.data )
# 			if ( is_submit :=request.data.get('is_submit', False) ) and is_submit == 'True': 
# 				instance = self.get_object()
# 				# 평가점수s = [ _inst.평가점수 for _inst in instance.ability_m2m.all() ]
# 				# instance.역량점수 =  round( sum(평가점수s)/len(평가점수s), 2)
# 				# instance.성과점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in instance.perform_m2m.all() ] )
# 				# instance.특별점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in instance.special_m2m.all() ] )
# 				# instance.save()

# 				QS_상급평가 = models.평가결과_DB.objects.exclude(id=instance.id).filter( 피평가자_평가체계_fk = instance.평가체계_fk )	
# 				ic ( QS_상급평가 )
# 				if QS_상급평가:
# 					for _inst in QS_상급평가:
# 						try:
# 							_inst.ability_m2m.clear()
# 							_inst.perform_m2m.clear()
# 							_inst.special_m2m.celar()
# 						except Exception as e:
# 							ic ('e')
# 						for m2m in instance.ability_m2m.all():
# 							_inst.ability_m2m.add (self.__m2m_save(m2m, _inst ))
# 						for m2m in instance.perform_m2m.all():
# 							_inst.perform_m2m.add (self.__m2m_save(m2m, _inst ))
# 						for m2m in instance.special_m2m.all():
# 							_inst.special_m2m.add (self.__m2m_save(m2m, _inst ))


# 		return super().update(request, *args, **kwargs )
	
# 	def __m2m_save(self, m2m, _inst):
# 		ic (_inst, _inst.평가체계_fk, _inst.평가체계_fk.평가자 )
# 		m2m.id = None
# 		m2m.평가점수 = 0
# 		m2m.등록자_fk = _inst.평가체계_fk.평가자
# 		m2m.save()
# 		return m2m


# class 상급자평가_DB_ViewSet(viewsets.ModelViewSet):

# 	MODEL = models.평가결과_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가결과_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.평가결과_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수__gte=1).order_by('-id')
	

# class 상급자평가_DB_API_View(APIView):
# 	MODEL = models.평가결과_DB

# 	def post(self, request, fromat=None ):
# 		평가설정_instance = models.평가설정_DB.objects.get(is_종료=False)
# 		QS = self.MODEL.objects.exclude(평가체계_fk__피평가자 = self.request.user).filter(평가체계_fk__평가설정_fk= 평가설정_instance ).filter(평가체계_fk__평가자 = self.request.user , 평가체계_fk__차수__gte=1).order_by('-id')
# 		차수별_대상자_dict = { 차수: self._get_IDs( QS.filter( 평가체계_fk__차수= 차수) ) for 차수  in range (1, 평가설정_instance.총평가차수+1) }
# 		차수별_is_submit = {  차수: self._get_is_submit( QS.filter( 평가체계_fk__차수= 차수) ) for 차수  in range (1, 평가설정_instance.총평가차수+1) }

# 		return Response ( status=status.HTTP_200_OK, data={'차수별_대상자' : 차수별_대상자_dict ,'차수별_유형': 평가설정_instance.차수별_유형, '차수별_is_submit': 차수별_is_submit })

# 	def _get_IDs (self, QS) -> list[int]:		
# 		return [ obj.id for obj in QS ]
# 	def _get_is_submit (self, QS) -> list[bool]:		
# 		return [ obj.is_submit for obj in QS ]

# class 역량_평가_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.역량_평가_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.역량_평가_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.역량_평가_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('fk__구분','fk__항목')
# 		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('fk__구분','fk__항목')
# 	def create(self, request, *args, **kwargs):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			request.data['등록자_fk'] = request.user.id
# 			request.data['등록자'] = datetime.now()
# 		return super().create( request, *args, **kwargs )

# 	def update(self, request, *args, **kwargs):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			request.data['등록자_fk'] = request.user.id
# 			request.data['등록자'] = datetime.now()
# 		return super().update( request, *args, **kwargs )

# class 성과_평가_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.성과_평가_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.성과_평가_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.성과_평가_DB_Filter

# 	def get_queryset(self):		
# 		return  self.MODEL.objects.order_by('-id')
# 		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('-id')
	
# class 특별_평가_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = models.특별_평가_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.특별_평가_DB_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.특별_평가_DB_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
# 		return  self.MODEL.objects.filter(등록자_fk = self.request.user ).order_by('-id')


# class Check_평가점수_API_View(APIView):
# 	MODEL = models.평가결과_DB

# 	def post(self, request, fromat=None ):
# 		if isinstance(request.data, QueryDict):  # optional
# 			request.data._mutable = True
# 			ID = int( request.data.get('id') )
# 			instance_평가결과 = models.평가결과_DB.objects.get( id = ID)

# 			역량check = self._check_역량 ( instance_평가결과.ability_m2m )
# 			성과check = self._check_성과_특별(instance_평가결과.perform_m2m )
# 			특별check = self._check_성과_특별(instance_평가결과.special_m2m )

# 			return Response(status=status.HTTP_200_OK,
# 				data= {'역량check':역량check, '성과check':성과check, '특별check':특별check })
	
# 	def _check_역량(self, ability_m2m) -> dict:		
# 		평가점수s = [ instance.평가점수 for instance in ability_m2m.all() ]
# 		return {'항목수': len( 평가점수s), '평가점수': round( sum(평가점수s)/len(평가점수s), 2)}

# 	def _check_성과_특별(self, m2m) -> dict:
# 		평가점수s = [ instance.평가점수*instance.가중치 / 100 for instance in m2m.all() ]
# 		가중치s =  [ instance.가중치 for instance in m2m.all() ]

# 		return {'가중치' : sum(가중치s),  '항목수': len( 평가점수s), '평가점수': round( sum(평가점수s), 2)  }
	
# class 종합평가_결과_API_View(APIView):
	
# 	def post(self, request, fromat=None ):
# 		if isinstance(request.data, QueryDict):  # optional
# 			ic (request.data )
# 			request.data._mutable = True
# 			퍙기설정_FK = int( request.data.get('평가설정_fk') )
# 			평가설정_Instance = models.평가설정_DB.objects.get( id = 퍙기설정_FK )

# 			df = pd.DataFrame(list( models.평가체계_DB.objects.filter( 평가설정_fk=평가설정_Instance, is_참여=True ).values() ))
# 			df = df.fillna( -1 )
# 			df = df.replace ( {np.nan: -1})

# 			df_pivot = (df.pivot_table(index=['피평가자_id'], columns=['차수'], values=['평가자_id']).astype(int) )

# 			df_reset = df_pivot
# 			df_reset.columns = df_reset.columns.droplevel()

# 			api_datas = df_reset.to_dict( orient='records')
# 			Users_QS =  User.objects.filter( is_active=True )
# 			##😀 api_datas : 평가체게에 대해
# 			QS_평가결과 = models.평가결과_DB.objects.filter ( 평가체계_fk__평가설정_fk = 평가설정_Instance)

# 			for obj in api_datas:
# 				for 차수 in range (평가설정_Instance.총평가차수+1):
# 					df_filter = df[(df['차수'] ==차수) & (df['피평가자_id'] == obj.get(0) )]
# 					차수_id =  int(df_filter.iloc[0]['id'])
# 					차수_평가자_id = int(df_filter.iloc[0]['평가자_id'])
# 					차수_평가자_성명 =  Users_QS.get(id=차수_평가자_id).user_성명 if 차수_평가자_id >0 else ''
# 					# ic ( obj, obj.get(0), '\n', df_filter )
# 					obj[f"{차수}_id"] = 차수_id 
# 					obj[f"{차수}_평가자_ID"] = 차수_평가자_id
# 					obj[f"{차수}_평가자_성명"] = 차수_평가자_성명

# 					_inst_평가결과 = QS_평가결과.get( 평가체계_fk_id = 차수_id)

# 					for name in ['id','is_submit', '역량점수','성과점수','특별점수','종합점수'] :						
# 						obj[f"{차수}_{name if name !='id' else '평가결과_id'}"] = getattr ( _inst_평가결과, name )

# 			차수별_점유:dict = 평가설정_Instance.차수별_점유
# 			for obj in api_datas:
# 				keyList = list ( obj.keys() )
# 				역량점수s = [ obj.get(name) for name in keyList if '역량점수' in str(name) ]
# 				성과점수s = [ obj.get(name) for name in keyList if '성과점수' in str(name) ]
# 				특별점수s = [ obj.get(name) for name in keyList if '특별점수' in str(name) ]
# 				종합점수s = [ obj.get(name) for name in keyList if '종합점수' in str(name) ]

# 				obj['최종_역량'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(역량점수s) ] )
# 				obj['최종_성과'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(성과점수s) ] )
# 				obj['최종_특별'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(특별점수s) ] )
# 				obj['최종_종합'] = sum( [ 점수* 차수별_점유.get(str(index) ) for index, 점수 in enumerate(종합점수s) ] )

# 			return Response(status=status.HTTP_200_OK, data=api_datas )
	

# class 평가설정DB_Old_ViewSet(viewsets.ModelViewSet):
# 	MODEL =  models_old.평가설정DB_Old
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.평가설정DB_Old_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	# search_fields =['평가체계_fk']
# 	# filterset_class =  customfilters.종합평가_결과_Old_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	

# class 종합평가_결과_Old_ViewSet(viewsets.ModelViewSet):
# 	MODEL =  models_old.종합평가_결과_Old
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.종합평가_결과_Old_Serializer
# 	filter_backends = [
# 		   SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	# search_fields =['평가체계_fk']
# 	filterset_class =  customfilters.종합평가_결과_Old_Filter

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')