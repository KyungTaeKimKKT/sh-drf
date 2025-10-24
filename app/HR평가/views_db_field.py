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
# from .customPage import CustomPagination
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
import pandas as pd
import json


from . import serializers
from . import models, models_old

from users.models import Api_App권한

import util.utils_func as Util

### const
TABLE_HEADER_역량평가사전_DB = ['id','구분','항목', '정의',]  ## 😀삭제 : 'is_master적용','is_개인별할당',

COLS_WIDTH_역량평가사전_DB = {
                        '구분'  : 16*10,
                        '항목' : 16*10,
                        '정의'  : 16*100,
                    }

TABLE_HEADER_평가설정_DB= ['id','제목','시작', '종료','is_시작','is_종료', '총평가차수','차수별_유형','차수별_점유','점유_역량','점유_성과','점유_특별'] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_평가설정_DB = {
					'제목' : 16*20,
                    }

class DB_Field_역량평가사전_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.역량평가사전_DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.역량평가사전_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_역량평가사전_DB,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_역량평가사전_DB,
			'no_vContextMenuCols' : TABLE_HEADER_역량평가사전_DB, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 작성(Update)합니다",
					"objectName" : 'new_row',
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
						['file'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 업로드",
					"tooltip" :"파일 업로드",
					"objectName" : 'file_upload',
					"enabled" : True,
				},
				'seperator':'',
				'파일_다운로드': {
					"position": (
						['file'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 다운로드",
					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
					"objectName" : 'file_download',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )


class DB_Field_평가설정_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.평가설정_DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.평가설정_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_평가설정_DB,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_평가설정_DB,
			'no_vContextMenuCols' : TABLE_HEADER_평가설정_DB, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 작성(Update)합니다",
					"objectName" : 'new_row',
					"enabled" : True,
				},
				'Copy':{
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "Copy",
					"tooltip" :"선택된 row를 copy하여 생성합니다.",
					"objectName" : 'copy_create_row',
					"enabled" : True,
				},
				'Delete': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "Delete",
					"tooltip" :"신규 작성합니다",
					"objectName" : 'Delete_row',
					"enabled" : True,
				},
				'section':'',
				'seperator':'',
				'평가쳬계_신규': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "평가체계_신규",
					"tooltip" :"평가체계를 신규 생성합니다",
					"objectName" : '평가체계_신규_row',
					"enabled" : True,
				},
				'section':'',
				'seperator':'',
				'평가쳬계_수정': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "평가체계_수정",
					"tooltip" :"평가체계를 신규 생성합니다",
					"objectName" : '평가체계_수정_row',
					"enabled" : True,
				},

				'section':'',
				'seperator':'',
				'평가항목_설정': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "평가항목_설정",
					"tooltip" :"평가항목을 생성합니다",
					"objectName" : '평가항목_설정_row',
					"enabled" : True,
				},
				'section':'',
				'seperator':'',
				'평가시스템_구축': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "평가시스템_구축",
					"tooltip" :"평가시스템을 db에 생성합니다",
					"objectName" : '평가시스템_구축_row',
					"enabled" : True,
				},

			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'파일_업로드': {
					"position": (
						['file'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 업로드",
					"tooltip" :"파일 업로드",
					"objectName" : 'file_upload',
					"enabled" : True,
				},
				'seperator':'',
				'파일_다운로드': {
					"position": (
						['file'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 다운로드",
					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
					"objectName" : 'file_download',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )



class DB_Field_역량_평가_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.역량_평가_DB
	TABLE_HEADER = ['id','구분','항목','정의', '평가점수']
	NO_EDIT_COLS =  ['id','구분','항목','정의' ]
	COLS_WIDTH = {
		'정의' : 16*40,
	}

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.역량_평가_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			'row_span_list' : ['구분',],
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )

class DB_Field_성과_평가_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.성과_평가_DB
	TABLE_HEADER = ['id','과제명','과제목표','성과', '목표달성률','실행기간','가중치','평가점수']
	NO_EDIT_COLS =  ['id', ]
	COLS_WIDTH = {
		'과제명' : 16*20,
		'과제목표': 16*20,
		'성과' :  16*30,
	}

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.성과_평가_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 작성(Update)합니다",
					"objectName" : 'new_row',
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
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	
class DB_Field_특별_평가_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.특별_평가_DB
	TABLE_HEADER = ['id','구분','성과','가중치', '평가점수',]
	NO_EDIT_COLS =  ['id', ]
	COLS_WIDTH = {
		'구분' : 16*10,
		'성과': 16*40,
	}

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.성과_평가_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 작성(Update)합니다",
					"objectName" : 'new_row',
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
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	

class DB_Field_상급자평가_개별_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.평가결과_DB
	TABLE_HEADER = ['id','평가체계_fk','피평가자','본인평가_id','본인평가_완료','피평가자_조직','피평가자_성명','is_submit','ability_m2m','perform_m2m','special_m2m','역량점수','성과점수','특별점수','종합점수']
	NO_EDIT_COLS =  ['id','평가체계_fk','본인평가_완료','피평가자_조직','피평가자_성명','is_submit', '역량점수','성과점수','특별점수','종합점수' ]
	COLS_WIDTH = {
		# '구분' : 16*10,
		# '성과': 16*40,
	}
	HIDDEN_COLS = [ '평가체계_fk', '피평가자','본인평가_id', 'ability_m2m','perform_m2m','special_m2m',]

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.평가결과_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {'본인평가_완료': 'BooleanField'},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' : HIDDEN_COLS,
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'인사평가': {
					"position": (
						['역량점수','성과점수','특별점수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "인사평가",
					"tooltip" :"인사평가",
					"objectName" : '인사평가',
					"enabled" : True,
				},



			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	

class DB_Field_상급자평가_종합_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.평가결과_DB
	TABLE_HEADER = ['id','평가체계_fk','피평가자','본인평가_id','본인평가_완료','피평가자_조직','피평가자_성명','is_submit','ability_m2m','perform_m2m','special_m2m','역량점수','성과점수','특별점수','종합점수']
	NO_EDIT_COLS =  ['id','평가체계_fk','본인평가_완료','피평가자_조직','피평가자_성명','is_submit', '종합점수' ]
	COLS_WIDTH = {
		# '구분' : 16*10,
		# '성과': 16*40,
	}
	HIDDEN_COLS = [ '평가체계_fk', '피평가자','본인평가_id', 'ability_m2m','perform_m2m','special_m2m',]
	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.평가결과_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' :  {'본인평가_완료': 'BooleanField'},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' : HIDDEN_COLS,
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	

class DB_Field_종합평가_결과_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models_old.종합평가_결과_Old
	# TABLE_HEADER = ['id','평가체계_fk','피평가자','본인평가_id','본인평가_완료','피평가자_조직','피평가자_성명','is_submit','ability_m2m','perform_m2m','special_m2m','역량점수','성과점수','특별점수','종합점수']
	# NO_EDIT_COLS =  ['id','평가체계_fk','피평가자_조직','피평가자_성명','is_submit', '종합점수' ]
	COLS_WIDTH = {
		# '구분' : 16*10,
		# '성과': 16*40,
	}

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.종합평가_결과_Old_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)
	api_data_예 ={'0': 158, '1': -1, '2': -1, '0_id': 1644, '0_평가자_ID': 158, '0_평가자_성명': '비정규', '0_평가결과_id': 998, '0_is_submit': False, '0_역량점수': 0.0, '0_성과점수': 0.0, '0_특별점수': 0.0, '0_종합점수': 0.0, '1_id': 1645, '1_평가자_ID': -1, '1_평가자_성명': '', '1_평가결과_id': 1107, '1_is_submit': False, '1_역량점수': 0.0, '1_성과점수': 0.0, '1_특별점수': 0.0, '1_종합점수': 0.0, '2_id': 1646, '2_평가자_ID': -1, '2_평가자_성명': '', '2_평가결과_id': 1221, '2_is_submit': False, '2_역량점수': 0.0, '2_성과점수': 0.0, '2_특별점수': 0.0, '2_종합점수': 0.0,}

	TABLE_HEADER = list ( api_data_예.keys() ) + ['최종_역량', '최종_성과', '최종_특별', '최종_종합' ]
	NO_EDIT_COLS =  TABLE_HEADER

	res_dict = {
        ###################################
		'fields_model' : model_field,		### 😀 tablemodel에서 self.header_type이 됨
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},				### 😀 tablemodel에서 self.header_type이 됨
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	


class DB_Field_종합평가_결과_Old_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models_old.종합평가_결과_Old
	# TABLE_HEADER = ['id','평가체계_fk','피평가자','본인평가_id','본인평가_완료','피평가자_조직','피평가자_성명','is_submit','ability_m2m','perform_m2m','special_m2m','역량점수','성과점수','특별점수','종합점수']
	# NO_EDIT_COLS =  ['id','평가체계_fk','피평가자_조직','피평가자_성명','is_submit', '종합점수' ]
	COLS_WIDTH = {
		# '구분' : 16*10,
		# '성과': 16*40,
	}

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.종합평가_결과_Old_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	TABLE_HEADER = list ( model_field.keys() )
	NO_EDIT_COLS =  TABLE_HEADER

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER ,
			'no_Edit_cols' : NO_EDIT_COLS,
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH ,
			'no_vContextMenuCols' : TABLE_HEADER, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	