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

from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from datetime import datetime, date,time, timedelta
import copy

from .serializers import *
from .models import *
import util.utils_func as Util


### CONST
TABLE_HEADER_망관리_DB = ['id', 'is_등록','망번호', '고객사','현장명','file수','문양','의장종류','할부치수','품명','망사','사용구분',
					   '세부내용','비고','검색key','등록일']
COLS_WIDTH_망관리_DB = {
                        # '현장명'  : 16*30,                        
                    }

TABLE_HEADER_망관리_DB_이력조회 = copy.deepcopy( TABLE_HEADER_망관리_DB )
TABLE_HEADER_망관리_DB_이력조회.remove('is_등록')

class  DB_Field_망관리_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = 망관리_DB
	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = 망관리_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {'file수': 'Integer'},
		'fields_delete' : {},
		'table_config' : {
			'table_header' : TABLE_HEADER_망관리_DB,
			'no_Edit_cols' :['id', '등록일'],
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_망관리_DB,
			'no_vContextMenuCols' :  TABLE_HEADER_망관리_DB,	### vContext menu를 생성하지 않는 col.
			'v_Menus' : {
				'section':'',
				'Export_to_Excel': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
					"title": "Export_to_excel",
					"tooltip" :"Excel로 table을 저장합니다.",
					"objectName" : 'Export_to_excel',
					"enabled" : True,
				},			
				'seperator':'',
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 작성합니다",
					"objectName" : 'New_row',
					"enabled" : True,
				},
				'Delete': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "Delete",
					"tooltip" :"신규 작성합니다",
					"objectName" : 'Delete_row',
					"enabled" : True,
				},
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'파일_업로드': {
					"position": (
						['file수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 업로드",
					"tooltip" :"파일 업로드",
					"objectName" : '파일_업로드',
					"enabled" : True,
				},
				'seperator':'',
				'파일_다운로드': {
					"position": (
						['file수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 다운로드",
					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
					"objectName" : '파일_다운로드',
					"enabled" : True,
				},
			}

		}
	}



	def get(self, request, format=None):
		# for key, field_type in self.serializer_field.items():
		# 	print ( key, type(field_type), field_type )
		print ( self.res_dict)
		return Response ( self.res_dict )
	
class  DB_Field_망관리_등록_View(DB_Field_망관리_DB_View):
	pass

class  DB_Field_망관리_이력조회_View(DB_Field_망관리_DB_View):
	MODEL = 망관리_DB
	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = 망관리_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {'file수': 'Integer'},
		'fields_delete' : {},
		'table_config' : {
			'table_header' : TABLE_HEADER_망관리_DB_이력조회,
			'no_Edit_cols' :TABLE_HEADER_망관리_DB_이력조회,
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_망관리_DB,
			'no_vContextMenuCols' :  TABLE_HEADER_망관리_DB_이력조회,	### vContext menu를 생성하지 않는 col.
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'파일_다운로드': {
					"position": (
						['file수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 다운로드",
					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
					"objectName" : '파일_다운로드',
					"enabled" : True,
				},
			}

		}
	}