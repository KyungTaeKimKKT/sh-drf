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


from . import serializers, models

from users.models import Api_App권한

import util.utils_func as Util

# ic.disable()

### const
TABLE_HEADER_작업지침_관리 = ['id','고객사','구분', '제목','Proj_No','is_배포','is_valid','Rev','변경사유_내용','prev_작지', '수량', '상세의장수','대표Render','의장도_수','첨부파일','납기일','작성일', '작성자_fk','작성자', '담당', '영업담당자_fk', '영업담당자', 
						'Rendering', '고객요청사항','고객성향','특이사항','집중점검항목','검사요청사항', ]


COLS_WIDTH_작업지침_관리 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_작업지침_의장Table = ['id', '적용부품','적용패널', 'Material','대표Process','상세Process','비고','표시순서', ]

COLS_WIDTH_작업지침_의장Table = {
                        # '구분'  : 16*10,
                        '상세Process' : 16*30,
                        '비고'  : 16*20,
                    }

# TABLE_HEADER_샘플관리_샘플관리 = TABLE_HEADER_샘플관리_샘플의뢰 + ['is_완료', '완료의견','완료일', '완료파일']

# COLS_WIDTH_샘플관리_샘플관리 = {
#                         # '구분'  : 16*10,
#                         # '항목' : 16*10,
#                         # '정의'  : 16*100,
#                     }

# TABLE_HEADER_샘플관리_샘플완료 = TABLE_HEADER_샘플관리_샘플의뢰 + ['is_완료']

# COLS_WIDTH_샘플관리_샘플완료 = {
#                         # '구분'  : 16*10,
#                         # '항목' : 16*10,
#                         # '정의'  : 16*100,
#                     }

class DB_Field_작업지침_관리_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.작업지침
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.작업지침_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'대표Render':'BooleanField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_작업지침_관리,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_작업지침_관리,
				'no_vContextMenuCols' : TABLE_HEADER_작업지침_관리, ### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
					'section':'',
					'seperator':'',
					'Form_New': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "New",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_new_row',
						"enabled" : True,
					},
					'Form_Update': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "수정",
						"tooltip" :"수정(Update)합니다",
						"objectName" : 'form_update_row',
						"enabled" : True,
					},
					'Form_View': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "보기",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_view_row',
						"enabled" : True,
					},

					'Delete': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "Delete",
						"tooltip" :"DB에서 삭제합니다.",
						"objectName" : 'Delete_row',
						"enabled" : True,
					},

					'ECO': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "ECO(변경사항)",
						"tooltip" :"ECO 발행합니다.",
						"objectName" : 'eco_row',
						"enabled" : True,
					},
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					'is_배포': {
						"position": (
							['is_배포'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "배포",
						"tooltip" :"배포",
						"objectName" : 'is_배포_cell',
						"enabled" : True,
					},
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['첨부파일','완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "파일 다운로드",
						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
						"objectName" : 'file_download_multiple',
						"enabled" : True,
					},
					'파일_View_Multiple': {
						"position": (
							['완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "완료결과_Preview",
						"tooltip" :"완료결과_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
					'update_의장도': {
						"position": (
							['의장도_수'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "의장도_update",
						"tooltip" :"의장도를 update할 수 있읍니다.",
						"objectName" : 'update_의장도',
						"enabled" : True,
					},
				}
			},

		}


class DB_Field_작업지침_등록_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.작업지침
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.작업지침_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'대표Render':'BooleanField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_작업지침_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_작업지침_관리, ['is_배포']),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_작업지침_관리,
				'no_vContextMenuCols' : TABLE_HEADER_작업지침_관리, ### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
					'section':'',
					'seperator':'',
					'Form_New': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "New",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_new_row',
						"enabled" : True,
					},
					'Form_Update': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "수정",
						"tooltip" :"수정(Update)합니다",
						"objectName" : 'form_update_row',
						"enabled" : True,
					},
					'Form_View': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "보기",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_view_row',
						"enabled" : True,
					},

					'Delete': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "Delete",
						"tooltip" :"DB에서 삭제합니다.",
						"objectName" : 'Delete_row',
						"enabled" : True,
					},

					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					# 'is_배포': {
					# 	"position": (
					# 		['is_배포'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "배포",
					# 	"tooltip" :"배포",
					# 	"objectName" : 'is_배포_cell',
					# 	"enabled" : True,
					# },
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['첨부파일','완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "파일 다운로드",
						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
						"objectName" : 'file_download_multiple',
						"enabled" : True,
					},
					'파일_View_Multiple': {
						"position": (
							['완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "완료결과_Preview",
						"tooltip" :"완료결과_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
					# 'update_의장도': {
					# 	"position": (
					# 		['의장도_수'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "의장도_update",
					# 	"tooltip" :"의장도를 update할 수 있읍니다.",
					# 	"objectName" : 'update_의장도',
					# 	"enabled" : True,
					# },
				}
			},

		}



class DB_Field_작업지침_ECO_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.작업지침
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.작업지침_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'대표Render':'BooleanField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_작업지침_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_작업지침_관리, ['is_배포']),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_작업지침_관리,
				'no_vContextMenuCols' : TABLE_HEADER_작업지침_관리, ### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
					'section':'',
					'seperator':'',
					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
					'Form_Update': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "수정",
						"tooltip" :"수정(Update)합니다",
						"objectName" : 'form_update_row',
						"enabled" : True,
					},
					'Form_View': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "보기",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_view_row',
						"enabled" : True,
					},

					'Delete': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "Delete",
						"tooltip" :"DB에서 삭제합니다.",
						"objectName" : 'Delete_row',
						"enabled" : True,
					},

					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					# 'is_배포': {
					# 	"position": (
					# 		['is_배포'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "배포",
					# 	"tooltip" :"배포",
					# 	"objectName" : 'is_배포_cell',
					# 	"enabled" : True,
					# },
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['첨부파일','완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "파일 다운로드",
						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
						"objectName" : 'file_download_multiple',
						"enabled" : True,
					},
					'파일_View_Multiple': {
						"position": (
							['완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "완료결과_Preview",
						"tooltip" :"완료결과_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
					# 'update_의장도': {
					# 	"position": (
					# 		['의장도_수'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "의장도_update",
					# 	"tooltip" :"의장도를 update할 수 있읍니다.",
					# 	"objectName" : 'update_의장도',
					# 	"enabled" : True,
					# },
				}
			},

		}


class DB_Field_작업지침_이력조회_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.작업지침
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.작업지침_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'대표Render':'BooleanField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_작업지침_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_작업지침_관리, []),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_작업지침_관리,
				'no_vContextMenuCols' : TABLE_HEADER_작업지침_관리, ### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
					'section':'',
					'seperator':'',
					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
					# 'Form_Update': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "수정",
					# 	"tooltip" :"수정(Update)합니다",
					# 	"objectName" : 'form_update_row',
					# 	"enabled" : True,
					# },
					'Form_View': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "보기",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_view_row',
						"enabled" : True,
					},

					# 'Delete': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "Delete",
					# 	"tooltip" :"DB에서 삭제합니다.",
					# 	"objectName" : 'Delete_row',
					# 	"enabled" : True,
					# },

					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					# 'is_배포': {
					# 	"position": (
					# 		['is_배포'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "배포",
					# 	"tooltip" :"배포",
					# 	"objectName" : 'is_배포_cell',
					# 	"enabled" : True,
					# },
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['첨부파일','완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "파일 다운로드",
						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
						"objectName" : 'file_download_multiple',
						"enabled" : True,
					},
					'파일_View_Multiple': {
						"position": (
							['완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "완료결과_Preview",
						"tooltip" :"완료결과_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
					# 'update_의장도': {
					# 	"position": (
					# 		['의장도_수'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "의장도_update",
					# 	"tooltip" :"의장도를 update할 수 있읍니다.",
					# 	"objectName" : 'update_의장도',
					# 	"enabled" : True,
					# },
				}
			},

		}



class DB_Field_작업지침_의장도Update_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.작업지침
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.작업지침_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'대표Render':'BooleanField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_작업지침_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_작업지침_관리, []),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_작업지침_관리,
				'no_vContextMenuCols' : TABLE_HEADER_작업지침_관리, ### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
					'section':'',
					'seperator':'',
					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
					# 'Form_Update': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "수정",
					# 	"tooltip" :"수정(Update)합니다",
					# 	"objectName" : 'form_update_row',
					# 	"enabled" : True,
					# },
					'Form_View': {
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "보기",
						"tooltip" :"신규 작성(Update)합니다",
						"objectName" : 'form_view_row',
						"enabled" : True,
					},

					# 'Delete': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "Delete",
					# 	"tooltip" :"DB에서 삭제합니다.",
					# 	"objectName" : 'Delete_row',
					# 	"enabled" : True,
					# },

					# 'ECO': {
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "ECO(변경사항)",
					# 	"tooltip" :"ECO 발행합니다.",
					# 	"objectName" : 'eco_row',
					# 	"enabled" : True,
					# },
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					# 'is_배포': {
					# 	"position": (
					# 		['is_배포'],	### table_header name
					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
					# 	),
					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					# 	"title": "배포",
					# 	"tooltip" :"배포",
					# 	"objectName" : 'is_배포_cell',
					# 	"enabled" : True,
					# },
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['첨부파일','완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "파일 다운로드",
						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
						"objectName" : 'file_download_multiple',
						"enabled" : True,
					},
					'파일_View_Multiple': {
						"position": (
							['완료파일'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "완료결과_Preview",
						"tooltip" :"완료결과_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
					'update_의장도': {
						"position": (
							['의장도_수'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "의장도_update",
						"tooltip" :"의장도를 update할 수 있읍니다.",
						"objectName" : 'update_의장도',
						"enabled" : True,
					},
				}
			},

		}




# class DB_Field_샘플관리_샘플의뢰_View(APIView):
# 	""" DB FILED VIEW {NAME:TYPE}"""

# 	def get(self, request, format=None):
# 		self._init_res_dict()
		
# 		return Response ( self.res_dict )
	
# 	def _init_res_dict(self):
# 		MODEL = models.샘플관리
# 		model_field = Util.get_MODEL_field_type(MODEL)

# 		_serializer = serializers.샘플관리_Serializer()
# 		serializer_field = Util.get_Serializer_field_type(_serializer)

# 		self.res_dict = {
# 			###################################

# 			'fields_model' : model_field,
# 			# 'fields_serializer' : serializer_field,
# 			'fields_append' : {},
# 			'fields_delete' : {},
# 			'table_config' : {
# 				#############
# 				'table_header' : TABLE_HEADER_샘플관리_샘플의뢰 ,
# 				'no_Edit_cols' : Util.get_List_deleted(TABLE_HEADER_샘플관리_샘플의뢰 ,['is_의뢰']),
# 				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
# 				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
# 				'hidden_columns' :[],
# 				'cols_width' : COLS_WIDTH_샘플관리_샘플의뢰,
# 				'no_vContextMenuCols' : TABLE_HEADER_샘플관리_샘플의뢰 , ### vContext menu를 생성하지 않는 col.
# 				'no_hContextMenuRows' :[],
# 				'v_Menus' : {
# 				},
# 				'h_Menus' : {
# 					'section':'',
# 					'seperator':'',
# 					'Form_New': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "New",
# 						"tooltip" :"신규 작성(Update)합니다",
# 						"objectName" : 'form_new_row',
# 						"enabled" : True,
# 					},
# 					'Form_Update': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "수정",
# 						"tooltip" :"수정(Update)합니다",
# 						"objectName" : 'form_update_row',
# 						"enabled" : True,
# 					},
# 					'Form_View': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "보기",
# 						"tooltip" :"신규 작성(Update)합니다",
# 						"objectName" : 'form_view_row',
# 						"enabled" : True,
# 					},

# 					'Delete': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "Delete",
# 						"tooltip" :"DB에서 삭제합니다.",
# 						"objectName" : 'Delete_row',
# 						"enabled" : True,
# 					},
# 				},
# 				'cell_Menus':{
# 					'section':'',
# 					'seperator':'',
# 					'파일_업로드_Multiple': {
# 						"position": (
# 							['첨부파일'],	### table_header name
# 							['all']		### 전체 경우, 'all' 아니면 rowNo
# 						),
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "파일 업로드",
# 						"tooltip" :"파일 업로드",
# 						"objectName" : 'file_upload_multiple',
# 						"enabled" : True,
# 					},
# 					'seperator':'',
# 					'파일_다운로드_Multiple': {
# 						"position": (
# 							['첨부파일'],	### table_header name
# 							['all']		### 전체 경우, 'all' 아니면 rowNo
# 						),
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "파일 다운로드",
# 						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
# 						"objectName" : 'file_download_multiple',
# 						"enabled" : True,
# 					},
# 				}
# 			},

# 		}



# class DB_Field_샘플관리_샘플완료_View(APIView):
# 	""" DB FILED VIEW {NAME:TYPE}"""

# 	def get(self, request, format=None):
# 		self._init_res_dict()
		
# 		return Response ( self.res_dict )
	
# 	def _init_res_dict(self):
# 		MODEL = models.샘플관리
# 		model_field = Util.get_MODEL_field_type(MODEL)

# 		_serializer = serializers.샘플관리_Serializer()
# 		serializer_field = Util.get_Serializer_field_type(_serializer)

# 		self.res_dict = {
# 			###################################

# 			'fields_model' : model_field,
# 			# 'fields_serializer' : serializer_field,
# 			'fields_append' : {},
# 			'fields_delete' : {},
# 			'table_config' : {
# 				#############
# 				'table_header' : TABLE_HEADER_샘플관리_샘플완료 ,
# 				'no_Edit_cols' : Util.get_List_deleted(TABLE_HEADER_샘플관리_샘플완료 ,['is_완료']),
# 				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
# 				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
# 				'hidden_columns' :[],
# 				'cols_width' : COLS_WIDTH_샘플관리_샘플의뢰,
# 				'no_vContextMenuCols' : TABLE_HEADER_샘플관리_샘플완료 , ### vContext menu를 생성하지 않는 col.
# 				'no_hContextMenuRows' :[],
# 				'v_Menus' : {
# 				},
# 				'h_Menus' : {
# 					'section':'',
# 					'seperator':'',
# 					# 'Form_New': {
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "New",
# 					# 	"tooltip" :"신규 작성(Update)합니다",
# 					# 	"objectName" : 'form_new_row',
# 					# 	"enabled" : True,
# 					# },
# 					# 'Form_Update': {
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "수정",
# 					# 	"tooltip" :"수정(Update)합니다",
# 					# 	"objectName" : 'form_update_row',
# 					# 	"enabled" : True,
# 					# },
# 					'Form_View': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "보기",
# 						"tooltip" :"신규 작성(Update)합니다",
# 						"objectName" : 'form_view_row',
# 						"enabled" : True,
# 					},

# 					# 'Delete': {
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "Delete",
# 					# 	"tooltip" :"DB에서 삭제합니다.",
# 					# 	"objectName" : 'Delete_row',
# 					# 	"enabled" : True,
# 					# },
# 				},
# 				'cell_Menus':{
# 					# 'section':'',
# 					# 'seperator':'',
# 					# '파일_업로드_Multiple': {
# 					# 	"position": (
# 					# 		['첨부파일'],	### table_header name
# 					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
# 					# 	),
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "파일 업로드",
# 					# 	"tooltip" :"파일 업로드",
# 					# 	"objectName" : 'file_upload_multiple',
# 					# 	"enabled" : True,
# 					# },
# 					# 'seperator':'',
# 					# '파일_다운로드_Multiple': {
# 					# 	"position": (
# 					# 		['첨부파일'],	### table_header name
# 					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
# 					# 	),
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "파일 다운로드",
# 					# 	"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
# 					# 	"objectName" : 'file_download_multiple',
# 					# 	"enabled" : True,
# 					# },
# 				}
# 			},

# 		}


# class DB_Field_샘플관리_이력조회_View(APIView):
# 	""" DB FILED VIEW {NAME:TYPE}"""

# 	def get(self, request, format=None):
# 		self._init_res_dict()
		
# 		return Response ( self.res_dict )
	
# 	def _init_res_dict(self):
# 		MODEL = models.샘플관리
# 		model_field = Util.get_MODEL_field_type(MODEL)

# 		_serializer = serializers.샘플관리_Serializer()
# 		serializer_field = Util.get_Serializer_field_type(_serializer)

# 		self.res_dict = {
# 			###################################

# 			'fields_model' : model_field,
# 			# 'fields_serializer' : serializer_field,
# 			'fields_append' : {},
# 			'fields_delete' : {},
# 			'table_config' : {
# 				#############
# 				'table_header' : TABLE_HEADER_샘플관리_샘플관리 ,
# 				'no_Edit_cols' : TABLE_HEADER_샘플관리_샘플관리,
# 				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
# 				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
# 				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
# 				'hidden_columns' :[],
# 				'cols_width' : COLS_WIDTH_샘플관리_샘플관리,
# 				'no_vContextMenuCols' : TABLE_HEADER_샘플관리_샘플관리 , ### vContext menu를 생성하지 않는 col.
# 				'no_hContextMenuRows' :[],
# 				'v_Menus' : {
# 				},
# 				'h_Menus' : {
# 					'Form_View': {
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "보기",
# 						"tooltip" :"신규 작성(Update)합니다",
# 						"objectName" : 'form_view_row',
# 						"enabled" : True,
# 					},
# 				},
# 				'cell_Menus':{
# 					'section':'',
# 					'seperator':'',
# 					# '파일_업로드_Multiple': {
# 					# 	"position": (
# 					# 		['첨부파일','완료파일'],	### table_header name
# 					# 		['all']		### 전체 경우, 'all' 아니면 rowNo
# 					# 	),
# 					# 	"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 					# 	"title": "파일 업로드",
# 					# 	"tooltip" :"파일 업로드",
# 					# 	"objectName" : 'file_upload_multiple',
# 					# 	"enabled" : True,
# 					# },
# 					'seperator':'',
# 					'파일_다운로드_Multiple': {
# 						"position": (
# 							['첨부파일','완료파일'],	### table_header name
# 							['all']		### 전체 경우, 'all' 아니면 rowNo
# 						),
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "파일 다운로드",
# 						"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
# 						"objectName" : 'file_download_multiple',
# 						"enabled" : True,
# 					},
# 					'파일_View_Multiple': {
# 						"position": (
# 							['완료파일'],	### table_header name
# 							['all']		### 전체 경우, 'all' 아니면 rowNo
# 						),
# 						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
# 						"title": "완료결과_Preview",
# 						"tooltip" :"완료결과_Preview 할 수 있습니다.",
# 						"objectName" : 'file_preview_multiple',
# 						"enabled" : True,
# 					},
# 				}
# 			},

# 		}







class DB_Field_작업지침_의장Table_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.Process

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.Process_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################

		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_작업지침_의장Table ,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :['id','표시순서'],
			'cols_width' : COLS_WIDTH_작업지침_의장Table ,
			'no_vContextMenuCols' : TABLE_HEADER_작업지침_의장Table , ### vContext menu를 생성하지 않는 col.
            'no_hContextMenuRows' :[],
			'v_Menus' : {
			},
			'h_Menus' : {
				'section':'',
				'seperator':'',
				'New': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "New",
					"tooltip" :"신규 row를 합니다",
					"objectName" : 'new_row',
					"enabled" : True,
				},

				'Delete': {
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "Delete",
					"tooltip" :"DB에서 삭제합니다.",
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

