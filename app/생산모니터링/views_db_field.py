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

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )
from . import serializers
# from . import customfilters
from . import models
from . import models_외부

from users.models import Api_App권한

import util.utils_func as Util

### const
TABLE_HEADER_생산계획실적 = ['id','line_no','생산capa', 'start_time','end_time','plan_qty','등록자']

COLS_WIDTH_생산계획실적 = {
                        'line_no'  : 16*10,
                        '생산capa' : 16*10,
                        'start_time'  : 16*15,
						'end_time'  : 16*15,
                    }

class DB_Field_생산계획실적_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = models_외부.생산계획실적

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.생산계획Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	model_field['start_time'] = 'TimeField'
	model_field['end_time'] = 'TimeField'
	res_dict = {
        ###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
            #############
			'table_header' : TABLE_HEADER_생산계획실적,
			'no_Edit_cols' :['id', 'line_no', '생산capa'],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'hidden_columns' :['id',],
			'cols_width' : COLS_WIDTH_생산계획실적,
			'no_vContextMenuCols' : TABLE_HEADER_생산계획실적, ### vContext menu를 생성하지 않는 col.
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

