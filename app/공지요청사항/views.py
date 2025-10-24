"""
Views for the 공지사항 APIs
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
import time
from django.db import transaction
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
from util.base_model_viewset import BaseModelViewSet
from django.db.models import Count, Q

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )

from .serializers import 공지사항_Serializer, 공지사항_Reading_Serializer, 요청사항_DB_Serializer,File_for_Request_Serializer

# from . import customfilters

from .models import (
	공지사항, 
	공지사항_Reading, 
	요청사항_DB,
	File_for_Request

)

from util.customfilters import *
from . import serializers
import util.utils_func as Util
import util.cache_manager as Cache_Manager
from util.redis_publisher import RedisPublisher
from django.utils import timezone

import logging, traceback
logger = logging.getLogger('공지요청사항')

class 공지사항_ViewSet(BaseModelViewSet):
	""" 공지사항 관리자용 view set """    
	MODEL = 공지사항
	APP_ID = 100
	use_cache = False
	queryset = MODEL.objects.all()
	serializer_class = 공지사항_Serializer
	parser_classes = [MultiPartParser,FormParser]

	filterset_class = 공지사항_FilterSet
	ordering_fields = ['popup_종료일','popup_시작일','종료일','시작일']
	ordering = ['-popup_종료일', '-popup_시작일', '-종료일', '-시작일']

	handle_name = '공지사항' ### config.models.WS_URLS_DB 의 name 필드 값으로 지정해야 함.

	def _perform_create(self, serializer):
		Cache_Manager.clear_all_cache_by_handle(handle=self.handle_name)
		return serializer.save()
	
	def _perform_update(self, serializer):
		Cache_Manager.clear_all_cache_by_handle(handle=self.handle_name)
		return serializer.save()
	
	def _perform_destroy(self, instance):
		Cache_Manager.clear_all_cache_by_handle(handle=self.handle_name)
		return instance.delete()

	def get_queryset(self):       
		return self.MODEL.objects.all()	
	
	@action(detail=False, methods=['get'], url_path='template')
	def template(self, request, *args, **kwargs):
		""" 템플릿 생성 """
		now = datetime.now()
		instance = self.MODEL()
		serializer = self.get_serializer(instance)
		data = serializer.data.copy()
		data['id'] = -1
		data['제목'] = '제목을 입력하세요'
		data['시작일'] = now.date().isoformat()
		data['종료일'] = (now.date() + timedelta(days=7)).isoformat()
		data['popup_시작일'] = now.date().isoformat()
		data['popup_종료일'] = (now.date() + timedelta(days=7)).isoformat()
		return Response(status=status.HTTP_200_OK, data= data )
		
	@action(detail=True, methods=['get'], url_path='request_ws_redis_publish')
	def request_ws_redis_publish(self, request, *args, **kwargs):
		""" 공지사항 발행 """
		try:	
			instance = self.get_object()
			serializer = self.get_serializer(instance)
			redis_publisher = RedisPublisher()
			_message = {
				"main_type" : "init",   # init / data / command / error 등
				"sub_type" : "notify",   # request / response / notify 등
				"action" : "popup",        # 세부 액션 정의
				"subject" : "공지사항", # 요청 대상이나 처리 도메인
				"message" :  serializer.data,           # payload (dict / list / None)
				"sender" : "server",         # "server", clinet_id:int
				"receiver" : "All",          # "All", [client_id1, client_id2, ...]
				"send_time" : datetime.now().isoformat(),
			}
			redis_publisher.publish(channel='broadcast:gongi', message=_message)
			return Response(status=status.HTTP_200_OK, data= {'message': '공지사항 발행 요청 전달됨'})
		except Exception as e:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= {'message': f'공지사항 발행 요청 실패: {e}'})
		
	@action(detail=True, methods=['get'], url_path='reading-save')
	def reading_save(self, request, *args, **kwargs):
		""" 공지사항 읽음 저장 """
		instance = self.get_object()
		user = request.user

		try:
			already_read = 공지사항_Reading.objects.filter(
				공지사항_fk=instance,
				user=user,
				timestamp__date=timezone.now().date()
			).exists()

			if user.is_admin:
				return Response(status=status.HTTP_200_OK, data={'message': '관리자 skip'})

			if not already_read:
				공지사항_Reading.objects.create(
					공지사항_fk=instance,
					user=user,
					ip=Util.get_client_ip(request),   #request.META.get('REMOTE_ADDR', ''),
					timestamp=timezone.now()
				)
				Cache_Manager.clear_all_cache_by_handle(handle=self.handle_name)
				return Response(status=status.HTTP_200_OK, data={'message': '공지사항 읽음 저장 완료'})
			else:
				return Response(status=status.HTTP_200_OK, data={'message': f"이미 읽음 처리됨 : { '관리자 skip' if user.is_admin else ''} "})

		except Exception as e:
			logger.exception(f"reading_save error for 공지사항 {instance.id} and user {user.id}: {e}")
			return Response(
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
				data={'message': f'공지사항 읽음 저장 실패: {e}'}
			)
		

class 공지사항_사용자_ViewSet(공지사항_ViewSet):
	APP_ID = 235
	http_method_names = ['get', 'post']


class 공지사항_Modal_ViewSet(공지사항_ViewSet):
	""" 공지사항 관리자용 view set """    
	queryset = 공지사항.objects.order_by('-id')
	serializer_class = 공지사항_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]

	def get_queryset(self):       
		today = date.today()
		user =  self.request.user
		# print (user.id, today)
		readingQS = 공지사항_Reading.objects.filter( user = user)
 
		qs = 공지사항.objects.filter(is_Popup=True, popup_시작일__lte = today, popup_종료일__gte = today ) \
			.exclude(id__in=list(readingQS.values_list('공지사항_fk_id', flat=True) )).order_by('-id')    
		return qs
	

class 공지사항_Reading_ViewSet(viewsets.ModelViewSet):
	""" 공지사항 reading 관리 view set """    
	queryset = 공지사항_Reading.objects.order_by('-id')
	serializer_class = 공지사항_Reading_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = 생산지시_Pagination

	def get_queryset(self):       
		qs = 공지사항_Reading.objects.all()
		return qs



class 요청사항_DB_ViewSet(BaseModelViewSet):
	MODEL = 요청사항_DB
	APP_ID = 149
	use_cache = False
	queryset = MODEL.objects.all()
	serializer_class = 요청사항_DB_Serializer
	parser_classes = [MultiPartParser,FormParser]
	search_fields =['제목','요청구분','내용',] 
	filterset_class = 요청사항_DB_FilterSet

	ordering_fields = ['요청등록일','처리일자']
	ordering = ['-요청등록일', '-처리일자']
	cache_base = '요청사항_DB'	


	def get_queryset(self):       
		return 요청사항_DB.objects.all()
	
	def perform_create(self, serializer):
		Cache_Manager.clear_all_cache(self.cache_base)
		is_완료 = serializer.validated_data.get('is_완료', False)
		if is_완료:
			serializer.save(
				등록자=self.request.user,
				요청등록일=timezone.now().date(),
				처리일자=timezone.now().date()
			)
		else:
			serializer.save(
				등록자=self.request.user,
				요청등록일=timezone.now().date()
			)

	def perform_update(self, serializer:serializers.요청사항_DB_Serializer):
		Cache_Manager.clear_all_cache(self.cache_base)
		is_완료 = serializer.validated_data.get('is_완료', False)
		print (is_완료)
		if is_완료:
			serializer.save(처리일자=timezone.now().date())
		else:
			serializer.save()

	def perform_destroy(self, instance:요청사항_DB):
		Cache_Manager.clear_all_cache(self.cache_base)
		instance.delete()

	@action(detail=False, methods=['get'], url_path='get_요청구분_list')
	def get_요청구분_list(self, request, *args, **kwargs):
		time_start = time.perf_counter()
		cache_key = f'{self.cache_base}:요청구분_list'
		data = Cache_Manager.get_cache(cache_key)
		if not data :
			default_list = ['기능개선 및 추가', '오류 및 버그 수정']
			exclude_list = default_list + ['기타']
			# default_list와 '기타'를 제외하고 count 순으로 정렬
			qs = (
				요청사항_DB.objects
				.exclude(요청구분__in=exclude_list)
				.values('요청구분')
				.annotate(count=Count('요청구분'))
				.order_by('-count')
			)
			db_list = [q['요청구분'] for q in qs]

			data = default_list + db_list + ['기타']
			Cache_Manager.set_cache(cache_key, data)
		time_end = time.perf_counter()
		print (f"요청구분 조회 소요시간: {1000*(time_end - time_start):.2f}msec")
		return Response(status=status.HTTP_200_OK, data=data)

	@action(detail=False, methods=['get'], url_path='template')
	def template(self, request, *args, **kwargs):
		""" 템플릿 생성 """
		now = timezone.now()
		instance = self.MODEL()
		serializer = self.get_serializer(instance)
		data = serializer.data.copy()
		data['id'] = -1
		data['제목'] = '제목을 입력하세요'
		data['요청등록일'] = now.date().isoformat()
		data['file수'] = 0
		data['files'] = []

		return Response(status=status.HTTP_200_OK, data= data )
	
	@action(detail=True, methods=['post','put','patch'], url_path='bulk')
	def bulk(self, request, pk=None, *args, **kwargs):
		""" 파일 업로드 """
		data = request.data.copy()
		try:
			ID = int(pk) if pk else int(data.pop('id', -1))
		except (ValueError, TypeError):
			ID = -1
		files = request.FILES.getlist('files')
		instance = None

		try:
			if ID > 0:
				instance = self.MODEL.objects.get(id=ID)
				serializer = self.get_serializer(instance=instance, data=data, partial=True)
			else:
				serializer = self.get_serializer(data=data)
		except self.MODEL.DoesNotExist:
			return Response({'message': f'ID {ID}에 해당하는 데이터 없음'}, status=status.HTTP_404_NOT_FOUND)

		with transaction.atomic():
			serializer.is_valid(raise_exception=True)
			if instance is None:
				self.perform_create(serializer)
			else:
				self.perform_update(serializer)

			instance = serializer.instance

			if files:
				file_objs = [
					File_for_Request(요청사항_fk=instance, file=file)
					for file in files
				]
				File_for_Request.objects.bulk_create(file_objs)
			
		serializer = self.get_serializer(instance)
		return Response(status=status.HTTP_200_OK, data=serializer.data)
	
class 요청사항_DB_사용자ViewSet(요청사항_DB_ViewSet):

	def get_queryset(self):       
		return 요청사항_DB.objects.all()
	

	
class File_for_Request_ViewSet(viewsets.ModelViewSet):
	queryset = File_for_Request.objects.order_by('-id')
	serializer_class = File_for_Request_Serializer
	parser_classes = [MultiPartParser,FormParser]

	def get_queryset(self):       
		return File_for_Request.objects.order_by('-id')