"""
Views for the scraping
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

from .models import (
	정부기관_DB,
	NEWS_DB,
	NEWS_Table_Head_DB,
	NEWS_LOG_DB,
)
from util.utils_viewset import Util_Model_Viewset
# from util.customfilters import NEWS_DB_FilterSet
from . import customfilters

import util.utils_func as Util


### CONST
TABLE_HEADER_NEWS_DB = ['id','정부기관','구분','제목','등록일','링크']

class DB_Field_NEWS_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = NEWS_DB
	authentication_classes = []
	permission_classes = []

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.NEWS_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            ####
			'table_header' : TABLE_HEADER_NEWS_DB,
			'no_Edit_cols' : TABLE_HEADER_NEWS_DB,
			'hidden_columns' :[],
			'no_vContextMenuCols' : TABLE_HEADER_NEWS_DB,	### vContext menu를 생성하지 않는 col.
            'cols_width' : {},
			'v_Menus' : {
				# 'section':'',
				# 'Export_to_Excel': {
				# 	"icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				# 	"title": "Export_to_excel",
				# 	"tooltip" :"Excel로 table을 저장합니다.",
				# 	"objectName" : 'Export_to_excel',
				# 	"enabled" : True,
				# },			
				# 'seperator':'',
			},
			'h_Menus' : {
				# 'section':'',
				# 'seperator':'',
				# 'New': {
				# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				# 	"title": "New",
				# 	"tooltip" :"신규 작성합니다",
				# 	"objectName" : 'New_row',
				# 	"enabled" : True,
				# },
				# 'Delete': {
				# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				# 	"title": "Delete",
				# 	"tooltip" :"신규 작성합니다",
				# 	"objectName" : 'Delete_row',
				# 	"enabled" : True,
				# },
			},
			'cell_Menus':{
				# 'section':'',
				# 'seperator':'',
				# '공지내용_수정': {
				# 	"position": (
				# 		['공지내용'],	### table_header name
				# 		['all']		### 전체 경우, 'all' 아니면 rowNo
				# 	),
				# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				# 	"title": "공지내용_수정",
				# 	"tooltip" :"공지내용_수정",
				# 	"objectName" : '공지내용_수정',
				# 	"enabled" : True,
				# },
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )


class 정부기관_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 정부기관_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.정부기관_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	


class NEWS_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = NEWS_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.NEWS_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	filterset_class = customfilters.NEWS_DB_FilterSet

	authentication_classes = []
	permission_classes = []

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class NEWS_Table_Head_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = NEWS_Table_Head_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.NEWS_Table_Head_DB_Serializer
	filter_backends = [
		#    SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	
class NEWS_LOG_DB_ViewSet(viewsets.ModelViewSet ):
	MODEL = NEWS_LOG_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.NEWS_LOG_DB_Serializer
	filter_backends = [
		#    SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
