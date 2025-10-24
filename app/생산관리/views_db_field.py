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
TABLE_HEADER_생산계획_일정관리 = ['id','생산지시_fk', '고객사','구분','Job_Name','Proj_No', 'schedule_door_fk','schedule_cage_fk','schedule_jamb_fk',
		'납기일_Door', '납기일_Cage', '납기일_JAMB', 
		  ]


COLS_WIDTH_생산계획_일정관리 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_생산계획_공정상세 = ['id','확정Branch_fk', '고객사','구분','Job_Name','Proj_No', '계획수량','소재','치수', '공정순서','공정명','ProductionLine_fk','구분','설비','name','계획일', 
		  ]


COLS_WIDTH_생산계획_공정상세 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_생산계획_공정상세_Merged = ['id','공정상세_ids', '확정Branch_fk', '고객사','구분','Job_Name','Proj_No', '계획수량','실적수량','소재','치수', '공정순서','공정명','ProductionLine_fk','공정구분','설비','설비명','계획일', 
		  ]


COLS_WIDTH_생산계획_공정상세_Merged = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }


class DB_Field_생산계획_일정관리_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산계획_일정관리
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산계획_일정관리_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'is_HTM_확정':'BooleanField', 'is_JAMB_확정':'BooleanField','납기일_Door': 'DateField','납기일_Cage':'DateField','납기일_JAMB':'DateField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_생산계획_일정관리,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산계획_일정관리 ,
				'no_vContextMenuCols' : TABLE_HEADER_생산계획_일정관리 ,### vContext menu를 생성하지 않는 col.
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




class DB_Field_생산계획_공정상세_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산계획_일정관리
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산계획_일정관리_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			## search ui
			'고객사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'is_HTM_확정':'BooleanField', 'is_JAMB_확정':'BooleanField','납기일_Door': 'DateField','납기일_Cage':'DateField','납기일_JAMB':'DateField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_생산계획_공정상세,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산계획_공정상세 ,
				'no_vContextMenuCols' : TABLE_HEADER_생산계획_공정상세 ,### vContext menu를 생성하지 않는 col.
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




class DB_Field_생산계획_공정상세_Merged_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.생산계획_공정상세
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.생산계획_공정상세_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)

		self.res_dict = {
			###################################
			# ## search ui
			# '고객사list' : ['현대','OTIS', 'TKE', '기타'],
			# '구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {'공정상세_ids':'ManyToManyField'},
			'fields_delete' : {},
			'table_config' : {

				#############
				'table_header' : TABLE_HEADER_생산계획_공정상세_Merged ,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_생산계획_공정상세_Merged ,
				'no_vContextMenuCols' : TABLE_HEADER_생산계획_공정상세_Merged  ,### vContext menu를 생성하지 않는 col.
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

