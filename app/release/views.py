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
from django.core.cache import cache
from django.utils import timezone
import json
import time as time_func

from release.serializers import Release관리_Serializer
from release.models import (
	Release관리
)

import util.utils_func as Util

from util.base_model_viewset import BaseModelViewSet

class Release관리_ViewSet(BaseModelViewSet):
	""" Release관리 view set """    
	MODEL = Release관리
	APP_ID = 130
	APP_INFO = {'div':'SW관리', 'name':'SW배포'}
	APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
	use_cache = False
	use_cache_permission = True
	cache_base = "Release 배포관리"
	cache_timeout = 60 * 60

	queryset = Release관리.objects.all()
	serializer_class = Release관리_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields = ['App이름','OS','버젼','종류']
	filterset_fields = ['App이름', 'OS']
	ordering_fields = ['timestamp','App이름','OS','버젼','종류']
	ordering = ['-timestamp','OS','버젼','종류']

	def get_queryset(self):       
		return Release관리.objects.order_by(*self.ordering)
	
	@action (detail=False, methods=['get'], url_path='template')
	def template(self, request, *args, **kwargs):
		""" 템플릿 생성 """
		instance = self.MODEL()
		serializer = self.get_serializer(instance)
		data = serializer.data.copy()
		data['id'] = -1
		data['timestamp'] = timezone.now().isoformat()

		return Response(status=status.HTTP_200_OK, data= data )

	@action (detail=True, methods=['get'], url_path='template_copyed')
	def template_copyed(self, request, *args, **kwargs):
		""" 템플릿 복사 """
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		data = serializer.data.copy()
		data['id'] = -data['id']
		data['timestamp'] = timezone.now().isoformat()
		data['is_release'] = False
		data['is_즉시'] = False
		data['변경사항'] = ''
		data['file'] = None
		data['버젼'] = float(data['버젼']) + 0.01

		return Response(status=status.HTTP_200_OK, data= data )

	
	@action(detail=False, methods=['get'], url_path='get_latest_release',permission_classes=[AllowAny])
	def get_latest_release(self, request, *args, **kwargs):
		start_time = time_func.time()
		# print ( 'params : ', request.query_params )
		app_name = request.query_params.get('App_name', None)
		os = request.query_params.get('OS', None)
		version = request.query_params.get('버젼', None)
		종류 = request.query_params.get('종류', None)

		if app_name is None or os is None or version is None or 종류 is None:
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':'App_name, OS, 버젼은 필수 입력 항목입니다.'})

		latest_release = self.get_queryset().filter(is_release=True, App이름=app_name, OS=os ,종류=종류).order_by('-id').first()
		if latest_release is None:
			print ( '최신 배포 버젼이 없습니다.' )
			return Response(status=status.HTTP_404_NOT_FOUND, data={'error':'최신 배포 버젼이 없습니다.'})
		
		if str(latest_release.버젼) == str(version):
			print ( '최신 배포 버젼입니다.' )
			return Response(status=status.HTTP_204_NO_CONTENT, data={'result':'최신 배포 버젼입니다.'})
		
		serializer = self.get_serializer(latest_release)
		# end_time = time_func.time()
		# print ( '소요시간 : ', end_time - start_time, '초' )
		return Response(status=status.HTTP_200_OK, data={'result':serializer.data})


class Release배포_ViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Release관리.objects.filter(is_release=True).order_by('-id')
	serializer_class = Release관리_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields = ['App이름',]
	filterset_fields = ['App이름', 'OS', '종류']
	permission_classes = []
	
	cache_key = 'sw_배포_list'  # 캐시 키
	cache_time = 60*60*12  # 캐시 유지 시간 (초)

	def get_queryset(self):       
		queryset = cache.get(self.cache_key)
		
		if queryset is None:
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = Release관리.objects.filter(is_release=True).order_by('-버젼')
			cache.set(self.cache_key, queryset, self.cache_time)
			print ( 'Release배포_ViewSet: no_cache : ', queryset.count() )
		return queryset
	
		return Release관리.objects.filter(is_release=True).order_by('-버젼')
	
	# https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
	# def create(self, request, *args, **kwargs):

	#     process_fks = json.loads( request.data.get('process_fks') )  if request.data.get('process_fks') else []
	#     첨부file_fks = request.FILES.getlist('첨부file_fks')  if request.FILES.getlist('첨부file_fks') else []
	#     의장도file_fks = json.loads( request.data.get('의장도file_fks') )  if request.data.get('의장도file_fks') else []
	#     el_info_fks = json.loads( request.data.get('el_info_fks') ) if request.data.get('el_info_fks') else []
	#     # print ( 'view 내, 참고사항file :', 참고사항file )
	#     # if isinstance(request.data, QueryDict):  # optional
	#     #     request.data._mutable = True
	#     #     request.data['영업담당자'] = request.user.user_성명

	#     serializer = self.get_serializer(data=request.data, 첨부file_fks=첨부file_fks, 의장도file_fks=의장도file_fks,
	#                                      process_fks=process_fks,el_info_fks=el_info_fks )
	#     # serializer = self.get_serializer(data=request.data)
	#     # main thing ends

	#     serializer.is_valid(raise_exception=True)
	#     self.perform_create(serializer)
	#     headers = self.get_success_headers(serializer.data)
	#     # return Response({'status': 200})
	#     return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	# def update(self, request, *args, **kwargs):
	#     # main thing starts
	#     instance = self.get_object()
	#     process_fks = json.loads( request.data.get('process_fks') ) if request.data.get('process_fks') else []
	#     결재내용_fks = json.loads( request.data.get('결재내용_fks') ) if  request.data.get('결재내용_fks') else []
	#     el_info_fks = json.loads( request.data.get('el_info_fks') ) if request.data.get('el_info_fks') else []
	#     첨부file_fks = request.FILES.getlist('첨부file_fks') if  request.FILES.getlist('첨부file_fks') else []
	#     의장도file_fks = request.FILES.getlist('의장도file_fks') if  request.FILES.getlist('의장도file_fks') else []

	#     serializer = self.get_serializer(instance, data=request.data, 첨부file_fks=첨부file_fks,el_info_fks=el_info_fks ,
	#                                       의장도file_fks=의장도file_fks, process_fks=process_fks, 결재내용_fks=결재내용_fks, partial=True )
	#     # main thing ends

	#     serializer.is_valid(raise_exception=True)
	#     self.perform_update(serializer)
	#     headers = self.get_success_headers(serializer.data)
	#     # return Response({'status': 200})
	#     return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
	
	# def destroy(self, request, *args, **kwargs):
	#     _instance = self.get_object()

	#     for obj in _instance.process_fks.all():
	#         obj.delete()

	#     _instance.delete()
	#     return Response(status=status.HTTP_204_NO_CONTENT)

