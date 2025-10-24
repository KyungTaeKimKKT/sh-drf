"""
Views for the SCM APIs
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
TABLE_HEADER_CS_Manage = ['id','el_info_fk','Elevator사','고객명','현장명','el수량','운행층수','부적합유형','불만요청사항','현장주소','고객연락처', '차수', '진행현황', '품질비용',
						  'claim_files_ids','claim_files_url','claim_file_수','activity_수','activity_files_ids','activity_files_url','activity_file_수','등록자_fk','등록자','등록일',
                          '완료자_fk','완료자','완료일',
	]

COLS_WIDTH__CS_Manage = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_CS_Claim_사용자_HIDDEN= [
	'id','el_info_fk', 'claim_files_ids', 'claim_files_url', 'activity_files_ids', 'activity_files_url', '등록자_fk','완료자_fk',]


TABLE_HEADER_CS_Claim_Activity = ['id','Elevator사','고객명','현장명','부적합유형','불만요청사항','현장주소','고객연락처', '차수', '진행현황', '품질비용',
								  'claim_files_url','claim_file_수','activity_id','예정_시작일','예정_완료일','활동현황','활동일','담당자','activity_files_url','activity_file_수','등록자_fk','등록자','등록일',
                                  '완료자_fk','완료자','완료일',
	]
COLS_WIDTH__CS_Claim_Activity = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }




TABLE_HEADER_CS_Activity = ['id','claim_fk','활동현황','활동일','등록자_fk','등록자','등록일','activity_files_ids','activity_file_수']
COLS_WIDTH__CS_Activity = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

class DB_Field_CS_Activity_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = models.CS_Activity
	_Serializer = serializers.CS_Activity_Serializer	

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		model_field = Util.get_MODEL_field_type(self.MODEL)

		serializer_field = Util.get_Serializer_field_type(self._Serializer())

		self.res_dict = {
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' :{
					'activity_files_ids':'JSONField',
					'activity_files_url':'JSONField',
					'claim_files_ids':'JSONField',
					'claim_files_url':'JSONField'
					} ,
			'fields_delete' : {},
			'table_config' : {
				'table_header' : TABLE_HEADER_CS_Activity,
				'no_Edit_cols' : TABLE_HEADER_CS_Activity,
				'no_Edit_rows' : ['ALL'], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH__CS_Activity ,
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
				}
			}
		}


class DB_Field_CS_Manage_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = models.CS_Manage
	_Serializer = serializers.CS_Manage_Serializer

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		model_field = Util.get_MODEL_field_type(self.MODEL)

		serializer_field = Util.get_Serializer_field_type(self._Serializer())

		self.res_dict = {
			###################################
			## search ui
			'Elevator사list' : ['현대','OTIS', 'TKE', '기타'],
			'구분list' : ['NE', 'MOD', '기타'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' :{'claim_files_ids':'JSONField'} ,
			'fields_delete' : {},
			'table_config' : {

				'Elevator사list' : ['현대','OTIS', 'TKE', '기타'],
				#############
				'table_header' : TABLE_HEADER_CS_Manage,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH__CS_Manage ,
				'no_vContextMenuCols' : TABLE_HEADER_CS_Manage ,### vContext menu를 생성하지 않는 col.
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
							['claim_file_수','activity_file_수'],	### table_header name
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
							['claim_file_수','activity_file수'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "File(image,pdf)_Preview",
						"tooltip" :"File(image,pdf)_Preview 할 수 있습니다.",
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


class DB_Field_CS_Claim_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = models.CS_Claim
	_Serializer = serializers.CS_Claim_Serializer

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		model_field = Util.get_MODEL_field_type(self.MODEL)

		serializer_field = Util.get_Serializer_field_type(self._Serializer())

		self.res_dict = {
			###################################
			## search ui
			'진행현황list' : ['작성','Open', 'Close'],

			##################################
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' :{
				'claim_files_ids':'JSONField',
				'claim_files_url':'JSONField',
				'activity_files_ids':'JSONField',
				'activity_files_url':'JSONField',
			} ,
			'fields_delete' : {},
			'table_config' : {

				'Elevator사list' : ['현대','OTIS', 'TKE', '기타'],
				#############
				'table_header' : TABLE_HEADER_CS_Manage,
				'no_Edit_cols' : TABLE_HEADER_CS_Manage,
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.white ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :['claim_files_url','activity_files_url'],
				'cols_width' : COLS_WIDTH__CS_Manage ,
				'no_vContextMenuCols' : TABLE_HEADER_CS_Manage ,### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
	
				},
				'cell_Menus':{
					'section':'',
					'seperator':'',
					'파일_다운로드_Multiple': {
						"position": (
							['claim_file_수','activity_file_수'],	### table_header name
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
							['claim_file_수','activity_file_수'],	### table_header name
							['all']		### 전체 경우, 'all' 아니면 rowNo
						),
						"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
						"title": "File(image,pdf)_Preview",
						"tooltip" :"File(image,pdf)_Preview 할 수 있습니다.",
						"objectName" : 'file_preview_multiple',
						"enabled" : True,
					},
				}
			},

		}

class DB_Field_CS_Claim_사용자_View(DB_Field_CS_Claim_View):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = models.CS_Claim
	_Serializer = serializers.CS_Claim_Serializer

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		super()._init_res_dict()
		model_field = Util.get_MODEL_field_type(self.MODEL)

		serializer_field = Util.get_Serializer_field_type(self._Serializer())
		self.res_dict['table_config']['no_Edit_cols'] = self.res_dict['table_config']['table_header']
		self.res_dict['table_config']['hidden_columns'] = TABLE_HEADER_CS_Claim_사용자_HIDDEN

		self.res_dict['table_config']['no_Edit_cols_color'] = "QtCore.QVariant( QtGui.QColor( '#ffffff' ))"



class DB_Field_CS_Claim_Activity_View(DB_Field_CS_Claim_View):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = models.CS_Claim
	_Serializer = serializers.CS_Claim_Serializer

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		model_field = Util.get_MODEL_field_type(self.MODEL)	
		serializer_field = Util.get_Serializer_field_type(self._Serializer())


		self.res_dict = {
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' :{
					'activity_files_ids':'JSONField',
					'activity_files_url':'JSONField',
					'claim_files_ids':'JSONField',
					'claim_files_url':'JSONField'
					} ,
			'fields_delete' : {},
			'table_config' : {
				'table_header' : TABLE_HEADER_CS_Claim_Activity,
				'no_Edit_cols' : TABLE_HEADER_CS_Claim_Activity,
				'no_Edit_rows' : ['ALL'], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.white ))",
				'hidden_columns' :['id','claim_files_url','activity_files_url','등록자_fk','완료자_fk','activity_id'],
				'cols_width' : COLS_WIDTH__CS_Claim_Activity ,
				'no_hContextMenuRows' :[],
				### row span 설정
				'row_span_list' : self._get_row_span_list(),
				'v_Menus' : {
				},
				'h_Menus' : {
				}
			}
		}		
	
	def _get_row_span_list(self):
		row_span_list = ['Elevator사','고객명','현장명','부적합유형','불만요청사항',
					   '현장주소','고객연락처', '차수', '진행현황', '품질비용','claim_file_수','등록자','등록일','완료자','완료일']
		row_span_list_with_sub = [ {'headerName':name, 'subHeader':'id'}     for name in row_span_list ]
		return row_span_list_with_sub