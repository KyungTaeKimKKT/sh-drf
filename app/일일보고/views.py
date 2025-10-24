"""
Views for the contact APIs
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
from django.db import transaction
from .customPage import CustomPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime, date,time, timedelta
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

import json
from .permissions import (
	개인_리스트_DB_전사_Permission,
	개인_리스트_DB_개인_Permission,
	조직_리스트_DB_전사_Permission,
	조직_리스트_DB_개인_Permission,
	전기사용량_DB_Permission,
	휴일등록_DB_Permission
)
from . import serializers
from . import customfilters
from util.base_model_viewset import BaseModelViewSet
from 일일보고.models import (
	ISSUE_리스트_DB,
	개인_리스트_DB, 
	휴일_DB,  
	조직_INFO,
	개인_INFO,
	전기사용량_DB,
)

from util.customfilters import *
from . import serializers
import util.utils_func as Util

import logging, traceback
logger = logging.getLogger(__name__)



def get_3days():
	""" 업무 보고를 위한 3일 날짜 가져옴"""
	# 오늘 날짜를 기준으로 캐시 키 생성
	today = datetime.now().date()
	cache_key = f'three_days_list_{today}'
	
	# 캐시에서 결과 확인
	cached_result = cache.get(cache_key)
	if cached_result:
		return cached_result

	day_list =[]
	day = today
	delta = timedelta(days=1)
	while ( len(day_list) <= 2 ):
		if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
		day -=delta
	day_list.reverse()
	return day_list

def _get_1Month(today=date.today()):
	lastDay =  today - timedelta(days=31) 
	return today - timedelta(days=31)

class Base_개인_리스트_DB_ViewSet(BaseModelViewSet):	
	MODEL = 개인_리스트_DB
	queryset = MODEL.objects.all()
	serializer_class = serializers.개인_리스트_DB_Serializer 
	ordering_fields = ['등록자_id__보고순서','일자', 'id']
	ordering = ['등록자_id__보고순서','일자', '-id']

	use_cache = False
	use_cache_permission = False

	@action(detail=False, methods=['get'], url_path='get_3days')
	def get_3days(self, request, *args, **kwargs):
		data_dict = { key:day for key, day in zip( ['어제','오늘','내일'], get_3days()) }
		return Response(status=status.HTTP_200_OK, data=data_dict)
	


class 개인_리스트_DB_전사_보고용_ViewSet(Base_개인_리스트_DB_ViewSet):
	""" 개인_리스트_DB view set for 3일"""    
	http_method_names = ['get', 'head', 'options'] 
	APP_ID = 37
	APP_INFO = {'div':'일일업무', 'name':'개인_전사'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	ordering_fields = ['등록자_id__보고순서','일자', 'id']
	ordering = ['등록자_id__보고순서','일자', '-id']


	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')

		return  queryset if not is_Create else 개인_리스트_DB.objects.exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		

class 개인_리스트_DB_개인_ViewSet(Base_개인_리스트_DB_ViewSet):
	""" 개인_리스트_DB view set for 3일"""    
	APP_ID = 39
	APP_INFO = {'div':'일일업무', 'name':'개인'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	ordering_fields = ['일자', 'id']
	ordering = ['일자', '-id']

	def get_queryset(self):
		day_list = getattr(self, 'day_list', get_3days() )
		queryset = ( 개인_리스트_DB.objects
			  .select_related('조직이름_id','등록자_id')
			  .filter(등록자_id__user_fk=self.request.user.id)
			  .filter(일자__in=day_list)
			  )
		return queryset

	def _ensure_entries_for_day_list(self):
		self.day_list = get_3days()
		qs = (
			개인_리스트_DB.objects
			.filter(등록자_id__user_fk=self.request.user.id, 일자__in=self.day_list)
		)

		for day in self.day_list :
			일자qs = qs.filter( 일자 = day) 
			if  not 일자qs.exists() : 
				개인_리스트_DB.objects.create ( 
					일자=day,
					등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
					조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)
					) ## 정상이면 foreingkey로 갔어야하는데...
			elif 일자qs.count() > 1:
				for _instance in 일자qs:
					if not (_instance.업무내용 and _instance.업무내용.strip()):
						_instance.delete()
		return qs

	
	def list(self, request, *args, **kwargs):
		self._ensure_entries_for_day_list()
		return super().list(request, *args, **kwargs)


	@action(detail=False, methods=['post','put','patch'], url_path='bulk')
	def bulk(self, request, *args, **kwargs):
		try:
			datas = json.loads(request.data.get('datas',[]))
			logger.info(f"datas: type{type(datas)} ; {datas}")
			if isinstance(datas, list) and datas:
				with transaction.atomic():
					for obj in datas:
						instance = None
						lookup_field = 'id'  # 혹은 unique한 다른 필드 사용
						obj['등록자_id'] = 개인_INFO.objects.get(user_fk=self.request.user.id).id
						obj['조직이름_id'] = 조직_INFO.objects.get(조직이름=self.request.user.기본조직1)

						if lookup_field in obj:
							try:
								if obj[lookup_field] and isinstance(obj[lookup_field], int) and obj[lookup_field] > 1:
									instance = self.get_queryset().get(**{lookup_field: obj[lookup_field]})								
								else:
									instance = None
							except self.get_queryset().model.DoesNotExist:
								instance = None
							finally:
								obj.pop(lookup_field, None)

						serializer = self.get_serializer(instance=instance, data=obj, partial=True)
						serializer.is_valid(raise_exception=True)
						serializer.save()

				return Response(status=status.HTTP_200_OK, data=self.list(request).data.get('results',[]))
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': 'no data'})
		except Exception as e:
			logger.error(f"Error: {e}")
			traceback.print_exc()
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': 'error'})

class 개인_리스트_DB_전사_조회_ViewSet(Base_개인_리스트_DB_ViewSet):
	""" 개인_리스트_DB view set for 조회"""   
	http_method_names = ['get', 'head', 'options'] 
	APP_ID = 53	
	APP_INFO = {'div':'일일업무', 'name':'개인이력조회(전사)'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)

	ordering_fields = ['일자', 'id']
	ordering = ['-일자', '-id']

	search_fields =['업무내용', '주요산출물','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.개인_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.MODEL.objects.order_by(*self.ordering)
		return queryset        
	

class 개인_리스트_DB_개인_조회_ViewSet(Base_개인_리스트_DB_ViewSet):
	""" 개인_리스트_DB view set for 조회만 가능하도록 METHOD 제한"""    
	http_method_names = ['get', 'head', 'options']
	APP_ID = 52
	APP_INFO = {'div':'일일업무', 'name':'개인이력조회'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	search_fields =['업무내용', '주요산출물','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정

	ordering_fields = ['일자', 'id']
	ordering = ['-일자', '-id']
	filterset_class =  customfilters.개인_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.MODEL.objects.filter(등록자_id__user_fk=self.request.user.id).order_by(*self.ordering)
		return queryset
	
class 개인_리스트_DB_팀별_조회_ViewSet(Base_개인_리스트_DB_ViewSet):
	http_method_names = ['get', 'head', 'options']
	APP_ID = 222
	APP_INFO = {'div':'일일업무', 'name':'개인이력조회_팀별'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)

	ordering_fields = ['일자', '등록자_id']
	ordering = ['-일자', '-등록자_id']
	def get_queryset(self):
		조직이름_id = 조직_INFO.objects.get(조직이름=self.request.user.기본조직1)
		queryset = self.MODEL.objects.filter(조직이름_id=조직이름_id).all()
		return queryset


class Base_조직_리스트_DB_ViewSet(BaseModelViewSet):	
	MODEL = ISSUE_리스트_DB
	queryset = MODEL.objects.all()
	serializer_class = serializers.조직_리스트_DB_Serializer 
	ordering_fields = ['등록자_id__보고순서','일자', 'id']
	ordering = ['등록자_id__보고순서','일자', '-id']

	search_fields =['활동현황', '세부내용','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.조직_리스트_DB_Filter 

	use_cache = False
	use_cache_permission = False

	@action(detail=False, methods=['get'], url_path='get_3days')
	def get_3days(self, request, *args, **kwargs):
		data_dict = { key:day for key, day in zip( ['어제','오늘','내일'], get_3days()) }
		return Response(status=status.HTTP_200_OK, data=data_dict)


class 조직_리스트_DB_전사_보고용_ViewSet(Base_조직_리스트_DB_ViewSet):
	""" 조직_리스트_DB view set for 3일"""    
	http_method_names = ['get', 'head', 'options']
	APP_ID = 40
	APP_INFO = {'div':'일일업무', 'name':'조직_전사'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	
	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		return ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','일자','등록자_id__보고순서')



class 조직_리스트_DB_개인_ViewSet(Base_조직_리스트_DB_ViewSet):
	""" 조직_리스트_DB view set for 3일"""    
	APP_ID = 41
	APP_INFO = {'div':'일일업무', 'name':'조직'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	

	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		queryset = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		for  day in day_list :
			if  not queryset.filter( 일자 = day)  : 
				is_Create = True
				ISSUE_리스트_DB.objects.create (pk = None, 일자=day,
										  등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
										  조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
		
		# return ISSUE_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		return  queryset if not is_Create else ISSUE_리스트_DB.objects.filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')

	@action(detail=False, methods=['post','put','patch'], url_path='bulk')
	def bulk(self, request, *args, **kwargs):
		try:
			datas = json.loads(request.data.get('datas',[]))
			logger.info(f"datas: type{type(datas)} ; {datas}")
			if isinstance(datas, list) and datas:
				with transaction.atomic():
					for obj in datas:
						instance = None
						lookup_field = 'id'  # 혹은 unique한 다른 필드 사용
						obj['등록자_id'] = 개인_INFO.objects.get(user_fk=self.request.user.id).id
						obj['조직이름_id'] = 조직_INFO.objects.get(조직이름=self.request.user.기본조직1)

						if lookup_field in obj:
							try:
								if obj[lookup_field] and isinstance(obj[lookup_field], int) and obj[lookup_field] > 1:
									instance = self.get_queryset().get(**{lookup_field: obj[lookup_field]})								
								else:
									instance = None
							except self.get_queryset().model.DoesNotExist:
								instance = None
							finally:
								obj.pop(lookup_field, None)

						serializer = self.get_serializer(instance=instance, data=obj, partial=True)
						serializer.is_valid(raise_exception=True)
						serializer.save()

				return Response(status=status.HTTP_200_OK, data=self.list(request).data.get('results',[]))
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': 'no data'})
		except Exception as e:
			logger.error(f"Error: {e}")
			traceback.print_exc()
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result': 'error'})

class 조직_리스트_DB_전사_조회_ViewSet(Base_조직_리스트_DB_ViewSet):
	""" 조직_리스트_DB view set for 조회"""    
	http_method_names = ['get', 'head', 'options'] 
	APP_ID = 55
	APP_INFO = {'div':'일일업무', 'name':'조직이력조회(전사)'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)

	ordering_fields = ['일자','조직이름_id__보고순서' 'id']
	ordering = ['-일자', '조직이름_id__보고순서', '-id']

	search_fields =['활동현황', '세부내용','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.조직_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.MODEL.objects.all()
		return queryset    


class 조직_리스트_DB_개인_조회_ViewSet(Base_조직_리스트_DB_ViewSet):
	""" 개인_리스트_DB view set for 조회"""  
	APP_ID = 54
	APP_INFO = {'div':'일일업무', 'name':'조직이력조회'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	ordering_fields = ['일자','조직이름_id__보고순서' 'id']
	ordering = ['-일자', '조직이름_id__보고순서', '-id']

	search_fields =['활동현황', '세부내용','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.조직_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.queryset.filter(등록자_id__user_fk=self.request.user.id).all()
		return queryset



class 전기사용량_ViewSet(BaseModelViewSet):
	MODEL = 전기사용량_DB
	APP_ID = 42
	APP_INFO = {'div':'일일업무', 'name':'전기사용량'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	use_cache = True
	cache_base = '일일보고_전기사용량'
	cache_timeout = 60*60*12
	queryset = 전기사용량_DB.objects.all()
	serializer_class = serializers.전기사용량_DB_Serializer 

	filterset_class =  customfilters.전기사용량_DB_Filter
	ordering_fields = ['일자','id']
	ordering = ['-일자', '-id']
	# permission_classes = [전기사용량_DB_Permission]

	# parser_classes = [MultiPartParser]
	# filter_backends = [
	# 	   SearchFilter, 
	# 	   filters.DjangoFilterBackend,
	# 	]
	# search_fields =['활동현황', '세부내용','비고'] # 👈 filters에 SearchFilter 지정
	# filterset_class =  customfilters.전기사용량_DB_Filter

	def _perform_create(self, serializer):
		serializer.save( 일자=timezone.now().date(), published_date=timezone.now(), 
				  등록자= self.request.user.user_성명	)
		return serializer.data
	
	def _perform_update(self, serializer):
		serializer.save( 일자=timezone.now().date(), published_date=timezone.now(), 
				  등록자= self.request.user.user_성명	)
		return serializer.data

	def get_queryset(self):
		return self.MODEL.objects.order_by(*self.ordering)
	

	


class 휴일등록_DB_개인_ViewSet(BaseModelViewSet):
	MODEL = 휴일_DB
	APP_ID = 56
	APP_INFO = {'div':'일일업무', 'name':'휴일등록(관리)'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	use_cache = True
	queryset = 휴일_DB.objects.all()
	serializer_class = serializers.휴일등록_DB__Serializer

	filterset_class =  customfilters.휴일_DB_Filter
	ordering_fields = ['휴일','id']
	ordering = ['-휴일', '-id']

	cache_base = '일일보고_휴일'  # 캐시 키
	cache_timeout = 60*60*12  # 캐시 유지 시간 (초)

	def _perform_create(self, serializer):
		self._validate_휴일(serializer=serializer)
		serializer.save()
		return serializer.data
	
	def _perform_update(self, serializer):
		self._validate_휴일(serializer=serializer)
		serializer.save()
		return serializer.data
	
	def _perform_destroy(self, instance):
		self._validate_휴일(instance=instance)
		instance.delete()
		return None
	
	def _validate_휴일(self, serializer=None, instance=None):
		if serializer:
			휴일 = serializer.validated_data.get('휴일')
		elif instance:
			휴일 = instance.휴일
		else:
			raise ValidationError({'휴일': '유효성 검사에 필요한 데이터가 없습니다.'})
		if 휴일 and 휴일 < timezone.now().date():
			raise ValidationError({'휴일': '과거 날짜의 휴일은 db 변경이 불가합니다.'})
	
	def get_queryset(self):       
		return self.MODEL.objects.order_by('-휴일')

	
