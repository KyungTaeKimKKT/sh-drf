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
TABLE_HEADER_영업수주_자재내역_To_의장 = ['id','자재내역','의장' 
		  ]


COLS_WIDTH_영업수주_자재내역_To_의장 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

TABLE_HEADER_영업수주_관리 = ['id','기준년월','is_confirmed','일정file','금액file','등록자_fk','등록자','created_at','updated_at','비고']
COLS_WIDTH_영업수주_관리 = {
                        # '구분'  : 16*10,
                        # '항목' : 16*10,
                        # '정의'  : 16*100,
                    }

class DB_Field_영업수주_관리DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

    
	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.영업수주_관리
		model_field = Util.get_MODEL_field_type(MODEL)
		
		_serializer = serializers.영업수주_관리_Serializer()
		serializer_field = Util.get_Serializer_field_type(_serializer)
		
		self.res_dict = {
			'fields_model' : model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				'table_header' : TABLE_HEADER_영업수주_관리,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_영업수주_관리 ,
				'no_vContextMenuCols' : TABLE_HEADER_영업수주_관리 ,### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
				},
				'cell_Menus':{
				}
			}

		}


class DB_Field_영업수주_자재내역_To_의장DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	def get(self, request, format=None):
		self._init_res_dict()
		
		return Response ( self.res_dict )
	
	def _init_res_dict(self):
		MODEL = models.자재내역_To_의장_Mapping
		model_field = Util.get_MODEL_field_type(MODEL)

		_serializer = serializers.자재내역_To_의장_Mapping_Serializer()
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
				'table_header' : TABLE_HEADER_영업수주_자재내역_To_의장,
				'no_Edit_cols' : ['id'],
				'no_Edit_rows' : [], ### row index : 0,1,2 들어감
				'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				# 'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
				'no_Edit_rows_color' : "QtCore.QVariant( QtGui.QColor( '#D4D4D4' ))",
				
				'hidden_columns' :[],
				'cols_width' : COLS_WIDTH_영업수주_자재내역_To_의장 ,
				'no_vContextMenuCols' : TABLE_HEADER_영업수주_자재내역_To_의장 ,### vContext menu를 생성하지 않는 col.
				'no_hContextMenuRows' :[],
				'v_Menus' : {
				},
				'h_Menus' : {
			
				},
				'cell_Menus':{
				}
			},

		}

