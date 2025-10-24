"""
Views for the serial APIs
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
# from datetime import datetime, date,time, timedelta
import datetime
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
from django.db.models import Q

from . import serializers
# from . import customfilters

from .models import (
	망관리_DB,
	# Process,
)
from util.utils_viewset import Util_Model_Viewset
from util.customfilters import 망관리_FilterSet



class 망관리_DB_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = 망관리_DB
	queryset = MODEL.objects.order_by('-망번호')
	serializer_class = serializers.망관리_DB_Serializer	
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields = ['망번호', '현장명','품명','세부내용','비고','검색key']
	filterset_class =  망관리_FilterSet

	def get_queryset(self):
		# from users.models import User
		# for _instance in self.MODEL.objects.order_by('-망번호'):
		# 	_instance.등록자_fk = User.objects.get(user_성명 = _instance.등록자 )
		# 	_instance.save()
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):
		"""  """
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['등록자'] = request.user.user_성명
			request.data['등록자_fk'] = request.user.id
			request.data['등록일'] = datetime.datetime.now()
			print ( self, request.data )
		return super().create( request, *args, **kwargs )
	

	# def get_queryset_by_request(self, request):       
	# 	생산계획_확정_Branch_fk = request.data.get('생산계획_확정_Branch_fk')
	# 	by_확정_branch_fk = Q(생산계획_확정_Branch_fk=생산계획_확정_Branch_fk)
	# 	return self.MODEL.objects.filter(by_확정_branch_fk).order_by('id')


class 망관리_등록_ViewSet(망관리_DB_ViewSet):
	# MODEL = 망관리_DB
	# queryset = MODEL.objects.order_by('-망번호')
	# serializer_class = serializers.망관리_DB_Serializer	
	# parser_classes = [MultiPartParser,FormParser]
	# filter_backends = [
	# 	   SearchFilter, 
	# 	   filters.DjangoFilterBackend,
	# 	]
	# search_fields = ['망번호', '현장명','품명','세부내용','비고','검색key']
	# filterset_class =  망관리_FilterSet

	def get_queryset(self):
		return  self.MODEL.objects.exclude(is_등록=True).filter(등록자_fk=self.request.user).order_by('-id')
	
class 망관리_이력조회_ViewSet(망관리_DB_ViewSet):
	# MODEL = 망관리_DB
	# queryset = MODEL.objects.order_by('-망번호')
	# serializer_class = serializers.망관리_DB_Serializer	
	# parser_classes = [MultiPartParser,FormParser]
	# filter_backends = [
	# 	   SearchFilter, 
	# 	   filters.DjangoFilterBackend,
	# 	]
	# search_fields = ['망번호', '현장명','품명','세부내용','비고','검색key']
	# filterset_class =  망관리_FilterSet

	def get_queryset(self):
		# for _instance in self.MODEL.objects.all():
		# 	_instance.is_등록 = True
		# 	_instance.save()
		return  self.MODEL.objects.filter(is_등록=True ).order_by('-id')
	