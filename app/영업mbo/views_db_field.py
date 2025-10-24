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
from . import models

from users.models import Api_App권한

import util.utils_func as Util

### const
TABLE_HEADER_영업mbo_설정 = ['id','매출_year','매출_month', 'is_검증','is_시작','is_완료', '현재_입력자','모든현장_금액_sum','신규현장_금액_sum', '기존현장_금액_sum',
			'모든현장_count', '기존현장_count', '신규현장_count', '등록자','등록일','file']  ## 😀삭제 : 'is_master적용','is_개인별할당',

COLS_WIDTH_영업mbo_설정 = {
                        # 'line_no'  : 16*10,
                        # '생산capa' : 16*10,
                        # 'start_time'  : 16*15,
						# 'end_time'  : 16*15,
                    }

TABLE_HEADER_영업mbo_사용자등록 = ['id','매출_year','매출_month', '현장명','고객사','구분', '기여도','비고' ,'sales_input_fk','sales_input_fks', 'admin_input_fk'] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_사용자등록 = {
					'비고' : 16*20,
                    }

TABLE_HEADER_영업mbo_관리자등록 = ['id','매출_year','매출_month', '현장명','고객사','구분', '기여도','비고' ,'등록자_ID','등록자_성명', 'sales_input_fk','sales_input_fks', 'admin_input_fk'] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_관리자등록 = {
					'비고' : 16*20,
                    }

month_list = [f'month_0{str(index)}' if index <10 else f'month_{str(index)}' for index in range(1,13)]
TABLE_HEADER_영업mbo_년간보고_지사_고객사 = ['id','매출년도','부서', '고객사','분류'] + month_list + ['합계' ] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_년간보고_지사_고객사  = {
					# '비고' : 16*20,
                    }

TABLE_HEADER_영업mbo_년간보고_지사_구분 = ['id','매출년도','부서', '구분','분류'] + month_list + ['합계' ,'지사_보고순서'] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_년간보고_지사_구분  = {
					# '비고' : 16*20,
                    }


TABLE_HEADER_영업mbo_년간보고_개인별 = ['id','매출년도','부서','담당자', '분류'] + month_list + ['합계' ,'개인_보고순서'] 
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_년간보고_개인별  = {
					# '비고' : 16*20,
                    }

TABLE_HEADER_영업mbo_이력조회 = ['id','매출_year','매출_month', '현장명','고객사','금액','구분', '부서','담당자','기여도','비고' ,]  
 ## 😀 부서, 담당자, 금액 등 제외

COLS_WIDTH_영업mbo_이력조회  = {
					# '비고' : 16*20,
                    }

class DB_Field_영업mbo_설정DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.영업mbo_설정DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.영업mbo_설정DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_영업mbo_설정,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_영업mbo_설정,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_설정, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'Update': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "Update",
					"tooltip" :"신규 작성(Update)합니다",
					"objectName" : 'Update_row',
					"enabled" : True,
				},
				'DB_초기화':{
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "DB초기화",
					"tooltip" :"적용된 db data를 초기화 합니다.",
					"objectName" : 'db_초기화',
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



class DB_Field_사용자등록_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.신규현장_등록_DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.신규현장_등록_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		###😀추가된 부분
		'고객사list' : [],
		'구분list' : [],
		'기여도list': [],

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'고객사list' : [],
			'구분list' :[],
			'기여도list': [],
            #############
			'table_header' : TABLE_HEADER_영업mbo_사용자등록,
			'no_Edit_cols' :['id','매출_year','매출_month','현장명','sales_input_fk','sales_input_fks','admin_input_fk', ],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :['id'],
			'cols_width' : COLS_WIDTH_영업mbo_사용자등록,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_사용자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'입력취소': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "입력취소",
					"tooltip" :"입력취소합니다.",
					"objectName" : 'clear_input',
					"enabled" : True,
				},
			},
			'cell_Menus':{
			}
		},

	}

	def get(self, request, format=None):
		self.res_dict['table_config']['고객사list' ] = list( models.고객사_DB.objects.all().values_list('고객사_id', flat=True) )
		self.res_dict['table_config']['구분list' ] = list( models.구분_DB.objects.all().values_list('구분_id', flat=True ) )
		self.res_dict['table_config']['기여도list' ] = list ( models.기여도_DB.objects.all().values_list('기여도_id', flat=True ) )
		return Response ( self.res_dict )



class DB_Field_관리자등록_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.신규현장_등록_DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.신규현장_등록_DB_관리자용_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		###😀추가된 부분
		'고객사list' : [],
		'구분list' : [],
		'기여도list': [],

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'고객사list' : [],
			'구분list' :[],
			'기여도list': [],
			'등록자_성명list' : [],
            #############
			'table_header' : TABLE_HEADER_영업mbo_관리자등록,
			'no_Edit_cols' :['id','매출_year','매출_month','현장명','등록자_ID','sales_input_fk','sales_input_fks','admin_input_fk', ],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_영업mbo_관리자등록,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'입력취소': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "입력취소",
					"tooltip" :"입력취소합니다.",
					"objectName" : 'clear_input',
					"enabled" : True,
				},
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		self.res_dict['table_config']['고객사list' ] = list( models.고객사_DB.objects.all().values_list('고객사_id', flat=True) )
		self.res_dict['table_config']['구분list' ] = list( models.구분_DB.objects.all().values_list('구분_id', flat=True ) )
		self.res_dict['table_config']['기여도list' ] = list ( models.기여도_DB.objects.all().values_list('기여도_id', flat=True ) )
		_instance_APP권한 = Api_App권한.objects.get(div='영업mbo', name='사용자등록' ) 
		등록자_성명list = [ user_fk.user_성명  for user_fk in _instance_APP권한.user_pks.all() ]
		self.res_dict['table_config']['등록자_성명list' ] = 등록자_성명list
		return Response ( self.res_dict )




class DB_Field_년간보고_지사_고객사_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.년간보고_지사_고객사

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.년간보고_지사_고객사_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	매출년도list = set(list( MODEL.objects.values_list('매출년도', flat=True) ) )

	res_dict = {
		###😀추가된 부분
		'매출년도list' : 매출년도list,
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'row_span_list' : ['부서',],

            #############
			'table_header' : TABLE_HEADER_영업mbo_년간보고_지사_고객사,
			'no_Edit_cols' : TABLE_HEADER_영업mbo_년간보고_지사_고객사,
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :['id'],
			'cols_width' : COLS_WIDTH_영업mbo_년간보고_지사_고객사,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )




class DB_Field_년간보고_지사_구분_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.년간보고_지사_구분

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.년간보고_지사_구분_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	매출년도list = set(list( MODEL.objects.values_list('매출년도', flat=True) ) )

	res_dict = {
		###😀추가된 부분
		'매출년도list' : 매출년도list,

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'row_span_list' : [ '부서', { 'headerName': '구분', 'subHeader':'부서'}, '분류' ],
            #############
			'table_header' : TABLE_HEADER_영업mbo_년간보고_지사_구분,
			'no_Edit_cols' : TABLE_HEADER_영업mbo_년간보고_지사_구분,
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :['id', '지사_보고순서'],
			'cols_width' : COLS_WIDTH_영업mbo_년간보고_지사_구분,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )



class DB_Field_년간보고_개인별_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.년간보고_개인별

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.년간보고_개인별_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	매출년도list = set(list( MODEL.objects.values_list('매출년도', flat=True) ) )

	res_dict = {
		###😀추가된 부분
		'매출년도list' : 매출년도list,

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			### type1 : str만 구성되면 해당 column만 row_span
			### type2 : {'headerName':str, 'subHeader':str } 형태면 2개를 merge해서  'headername' column row_span,
			'row_span_list' : ['부서','담당자'],

            #############
			'table_header' : TABLE_HEADER_영업mbo_년간보고_개인별,
			'no_Edit_cols' : TABLE_HEADER_영업mbo_년간보고_개인별,
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :['id','개인_보고순서'],
			'cols_width' : COLS_WIDTH_영업mbo_년간보고_개인별,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )



class DB_Field_년간목표입력_지사_구분_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.년간보고_지사_구분

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.년간보고_지사_구분_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	매출년도list = set(list( MODEL.objects.values_list('매출년도', flat=True) ) )

	res_dict = {
		###😀추가된 부분
		'매출년도list' : sorted(매출년도list, reverse=True),

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'row_span_list' : [ '부서', { 'headerName': '구분', 'subHeader':'부서'}, '분류' ],
            #############
			'table_header' : TABLE_HEADER_영업mbo_년간보고_지사_구분,
			'no_Edit_cols' : ['id', '매출년도','구분','분류','합계'],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_영업mbo_년간보고_지사_구분,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )




class DB_Field_년간목표입력_개인별_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.년간보고_개인별

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.년간보고_개인별_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)
	
	매출년도list = set(list( MODEL.objects.values_list('매출년도', flat=True) ) )

	res_dict = {
		'매출년도list' : sorted(매출년도list, reverse=True),

        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			### type1 : str만 구성되면 해당 column만 row_span
			### type2 : {'headerName':str, 'subHeader':str } 형태면 2개를 merge해서  'headername' column row_span,
			'row_span_list' : ['부서','담당자'],

            #############
			'table_header' : TABLE_HEADER_영업mbo_년간보고_개인별,
			'no_Edit_cols' : ['id','매출년도','부서','담당자','분류','합계',],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_영업mbo_년간보고_개인별,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_관리자등록, ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'등록자_선택': {
					"position": (
						['sales_input_fks'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "등록자_선택",
					"tooltip" :"등록자_선택",
					"objectName" : '등록자_선택',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )


class DB_Field_이력조회_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.출하현장_master_DB

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.출하현장_master_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)
	
	QS = MODEL.objects.all()
	고객사list = set(list(models.고객사_DB.objects.all().values_list('고객사_id', flat=True)))
	구분list =  set(list(models.구분_DB.objects.exclude(구분_id='TOTAL').values_list('구분_id', flat=True)))
	부서list = set( list(QS.values_list('부서', flat=True)))
	담당자list = set( list(QS.values_list('담당자', flat=True)))

	print ( 고객사list, 구분list,  부서list, 담당자list)
	res_dict = {
		###😀추가된 부분
		'고객사list' : 고객사list,
		'구분list' : 구분list,
		'부서list': 부서list,
		'담당자list': 담당자list,
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			### type1 : str만 구성되면 해당 column만 row_span
			### type2 : {'headerName':str, 'subHeader':str } 형태면 2개를 merge해서  'headername' column row_span,
			# 'row_span_list' : ['부서','담당자'],

            #############
			'table_header' : TABLE_HEADER_영업mbo_이력조회,
			'no_Edit_cols' : TABLE_HEADER_영업mbo_이력조회,
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :[],
			'cols_width' : COLS_WIDTH_영업mbo_이력조회,
			'no_vContextMenuCols' : TABLE_HEADER_영업mbo_이력조회, ### vContext menu를 생성하지 않는 col.
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


