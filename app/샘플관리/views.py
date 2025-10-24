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

# class 차량관리_차량번호_사용자_API_View ( APIView):	
# 	def get(self, request, format=None):
# 		q_filters =  Q( write_users_m2m__in = [request.user]) | Q( admin_users_m2m__in = [request.user] )
# 		차량번호 = set(list(models.차량관리_기준정보.objects.filter( q_filters). values_list('차량번호', flat=True)))
# 		ic ( 차량번호 )
# 		return Response ( 차량번호 )

class 샘플관리_샘플관리_ViewSet(viewsets.ModelViewSet):
	MODEL = models.샘플관리
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.샘플관리_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['고객사','요청건명','용도_현장명']
	# filterset_class =  역량평가사전_DB_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	# def create(self, request, *args, **kwargs):
	# 	ic ( request.data )
	# 	if isinstance(request.data, QueryDict):  # optional
	# 		request.data._mutable = True
	# 		request.data['요청자_fk'] = self.request.user.id
	# 	ic ( request.data )
	# 	return super().create(request, *args, **kwargs )

class 샘플관리_샘플의뢰_ViewSet(샘플관리_샘플관리_ViewSet):

	def get_queryset(self):
		return  self.MODEL.objects.filter(is_의뢰=False).order_by('-id')
	
	def create(self, request, *args, **kwargs):
		ic ( request.data )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['요청자_fk'] = self.request.user.id
		ic ( request.data )
		return super().create(request, *args, **kwargs )

class 샘플관리_샘플완료_ViewSet(샘플관리_샘플관리_ViewSet):

	def get_queryset(self):
		return  self.MODEL.objects.filter(is_의뢰=True, is_완료=False).order_by('-id')
	
	def update(self, request, *args, **kwargs):
		ic ( request.data )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['완료자_fk'] = self.request.user.id
			request.data['완료일'] = datetime.now()
		ic ( request.data )
		return super().update(request, *args, **kwargs )

class 샘플관리_이력조회_ViewSet(샘플관리_샘플관리_ViewSet):

	def get_queryset(self):
		return  self.MODEL.objects.filter(is_의뢰=True ).order_by('-id')



class 샘플관리_Process_ViewSet(viewsets.ModelViewSet):
	MODEL = models.Process
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.Process_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['차량번호','차종']
	filterset_class =  customfilters.샘플관리_Process_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('표시순서')
	

class 샘플관리_첨부file_ViewSet(viewsets.ModelViewSet):
	MODEL = models.첨부file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.첨부file_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['차량번호','차종']
	# filterset_class =  customfilters.샘플관리_Process_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('id')
	
class 샘플관리_완료file_ViewSet(viewsets.ModelViewSet):
	MODEL = models.완료file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.완료file_Serializer
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['차량번호','차종']
	# filterset_class =  customfilters.샘플관리_Process_Filter

	def get_queryset(self):
		return  self.MODEL.objects.order_by('id')
