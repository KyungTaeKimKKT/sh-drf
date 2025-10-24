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
import 생산관리.models as 생산관리Models

from users.models import Api_App권한

import util.utils_func as Util

# ic.disable()

### const
TABLE_HEADER_생산지시_관리 = ['id','생산형태','고객사','구분', 'Job_Name','Proj_No','is_배포','is_valid','Rev','변경사유_내용','prev_생지', 
		'총수량', '지시수량', '차수','납기일_Door','납기일_Cage', '상세의장수','호기_수','HTM_Sheet','is_HTM_확정','JAMB_Sheet','is_JAMB_확정','생산지시일','소재발주일', '작업지침', '작성일', '작성자_fk','작성자', 
		'작업지침_fk', 'NCR_fk', 'JAMB_발주정보_fk', 'tab_made_fks', '도면정보_fks', 'process_fks','spg_fks',
		  ]


COLS_WIDTH_생산지시_관리 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_생산지시_의장Table = ['id', '생산처','적용','소재','치수','수량','대표Process','상세Process','출하처','비고','확정','작지Process_fk','구분','표시순서' ]

COLS_WIDTH_생산지시_의장Table = {
                        # '구분'  : 16*10,
                        '상세Process' : 16*30,
                        '비고'  : 16*20,
                    }

TABLE_HEADER_생산지시_도면정보Table = ['id', '공사번호', '호기','현장명','사양','발주일','납기일_Door','납기일_Cage', '인승','JJ', 'CH', 'HH', 
		'HD_기타층_수량1','HD_기타층_수량2', 'HD_기준층_수량1','HD_기준층_수량2','CD_수량1','CD_수량2', 'CW_수량1','CW_수량2', '상판_수량1','상판_수량2', 
		'표시순서' ]

COLS_WIDTH_생산지시_도면정보Table = {
                        # '구분'  : 16*10,
                        # '상세Process' : 16*30,
                        # '비고'  : 16*20,
                    }



TABLE_HEADER_생산지시_도면정보Table_Body = ['id', '공사번호', '호기','현장명','사양','발주일','납기일_Door','납기일_Cage', '인승','JJ', 'CH', 'HH', 
		'HD_기타층_수량1','HD_기타층_수량2', 'HD_기준층_수량1','HD_기준층_수량2','CD_수량1','CD_수량2', 'CW_수량1','CW_수량2', '상판_수량1','상판_수량2', 
		'표시순서' ]

COLS_WIDTH_생산지시_도면정보Table_Body = {
                        # '구분'  : 16*10,
                        # '상세Process' : 16*30,
                        # '비고'  : 16*20,
                    }

TABLE_HEADER_생산지시_SPG_Table = ['id', '품번', '측판폭_W','소재폭_W0','길이_L','소재길이_A0','밴딩W_T','밴딩A_T','W1','A1','W2','A2','W3','A3','대표Process','상세Process',
		'표시순서' ]

COLS_WIDTH_생산지시_SPG_Table = {
                        # '구분'  : 16*10,
                        '상세Process' : 16*30,
                        # '비고'  : 16*20,
                    }

class DB_Field_생산지시_관리_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산지시
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산지시_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'is_HTM_확정':'BooleanField', 'is_JAMB_확정':'BooleanField','납기일_Door': 'DateField','납기일_Cage':'DateField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_생산지시_관리,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산지시_관리,
				'no_vContextMenuCols' : TABLE_HEADER_생산지시_관리, ### vContext menu를 생성하지 않는 col.
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


class DB_Field_생산지시_등록_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산지시
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산지시_Serializer()
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
				'table_header' : TABLE_HEADER_생산지시_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_생산지시_관리, ['is_배포']),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산지시_관리,
				'no_vContextMenuCols' : TABLE_HEADER_생산지시_관리, ### vContext menu를 생성하지 않는 col.
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



class DB_Field_생산지시_ECO_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산지시
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산지시_Serializer()
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
				'table_header' : TABLE_HEADER_생산지시_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_생산지시_관리, ['is_배포']),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산지시_관리,
				'no_vContextMenuCols' : TABLE_HEADER_생산지시_관리, ### vContext menu를 생성하지 않는 col.
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


class DB_Field_생산지시_이력조회_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산지시
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산지시_Serializer()
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
				'table_header' : TABLE_HEADER_생산지시_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_생산지시_관리, []),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산지시_관리,
				'no_vContextMenuCols' : TABLE_HEADER_생산지시_관리, ### vContext menu를 생성하지 않는 col.
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



class DB_Field_생산지시_의장도Update_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산지시
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산지시_Serializer()
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
				'table_header' : TABLE_HEADER_생산지시_관리,
				'no_Edit_cols' : Util.get_List_deleted( TABLE_HEADER_생산지시_관리, []),
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산지시_관리,
				'no_vContextMenuCols' : TABLE_HEADER_생산지시_관리, ### vContext menu를 생성하지 않는 col.
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


class DB_Field_생산지시_의장Table_View(APIView):
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
			'치수_LIST' : list(set(MODEL.objects.order_by('치수').values_list('치수', flat=True))), 
			'판금처_LIST' : list(set(생산관리Models.판금처_DB.objects.order_by('id').values_list('판금처', flat=True))), 
            #############
			'table_header' : TABLE_HEADER_생산지시_의장Table ,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :['id','표시순서'],
			'cols_width' : COLS_WIDTH_생산지시_의장Table ,
			'no_vContextMenuCols' : TABLE_HEADER_생산지시_의장Table , ### vContext menu를 생성하지 않는 col.
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


class DB_Field_생산지시_도면정보Table_Body_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.도면정보

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.도면정보_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################

		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_생산지시_도면정보Table_Body ,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :['id','표시순서'],
			'cols_width' : COLS_WIDTH_생산지시_도면정보Table_Body ,
			'no_vContextMenuCols' : TABLE_HEADER_생산지시_도면정보Table_Body , ### vContext menu를 생성하지 않는 col.
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


class DB_Field_생산지시_SPG_Table_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models.SPG_Table

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.SPG_Table_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
        ###################################

		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_생산지시_SPG_Table ,
			'no_Edit_cols' :['id', ],
			'no_Edit_rows' : [], ### row index : 0,1,2 들어감
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
			
			'hidden_columns' :['id','표시순서'],
			'cols_width' : COLS_WIDTH_생산지시_SPG_Table ,
			'no_vContextMenuCols' : TABLE_HEADER_생산지시_SPG_Table , ### vContext menu를 생성하지 않는 col.
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

