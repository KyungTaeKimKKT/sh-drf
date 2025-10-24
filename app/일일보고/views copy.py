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
from .customPage import CustomPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime, date,time, timedelta
from django.core.cache import cache
from django.db.models import Count

from .permissions import (
	개인_리스트_DB_전사_Permission,
	개인_리스트_DB_개인_Permission,
	조직_리스트_DB_전사_Permission,
	조직_리스트_DB_개인_Permission,
	전기사용량_DB_Permission,
	휴일등록_DB_Permission
)
from . import serializers
from . import customfilters

from 일일보고.models import (
	ISSUE_리스트_DB,
	개인_리스트_DB, 
	휴일_DB,  
	조직_INFO,
	개인_INFO,
	전기사용량_DB,
)

from util.customfilters import *
from . import serializers
import util.utils_func as Util

### CONST
TABLE_HEADER_개인LIST = ['id', '조직이름_id', '일자','업무내용','업무주기','소요시간','주요산출물','비고']
COLS_WIDTH_개인LIST = {
						'업무내용'  : 16*30,
						'주요산출물' : 16*30,
						'비고'     : 16*25,
					}

TABLE_HEADER_개인_보고용 = ['id', '조직', '보고자','일자','업무내용','업무주기','소요시간','주요산출물','비고']

TABLE_HEADER_조직LIST = ['id', '조직이름_id', '일자','활동현황','세부내용','완료예정일','진척율','유관부서','비고']
COLS_WIDTH_조직LIST = {
						'활동현황'  : 16*30,
						'세부내용' : 16*30,
						'유관부서'  : 16*15,
						'비고'     : 16*25,
					}

TABLE_HEADER_조직_보고용 = ['id', '조직', '일자','활동현황','세부내용','완료예정일','진척율','유관부서','비고']


def get_3days():
	""" 업무 보고를 위한 3일 날짜 가져옴"""
	# 오늘 날짜를 기준으로 캐시 키 생성
	today = datetime.now().date()
	cache_key = f'three_days_list_{today}'
	
	# 캐시에서 결과 확인
	cached_result = cache.get(cache_key)
	if cached_result:
		return cached_result

	day_list =[]
	day = today
	delta = timedelta(days=1)
	while ( len(day_list) <= 2 ):
		if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
		day -=delta
	day_list.reverse()
	return day_list

def _get_1Month(today=date.today()):
	lastDay =  today - timedelta(days=31) 
	return today - timedelta(days=31)

class 개인_리스트_DB_전사_ViewSet(viewsets.ModelViewSet):
	""" 개인_리스트_DB view set for 3일"""    
	qs = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	serializer_class = serializers.개인_리스트_DB_Serializer 
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['업무내용', '주요산출물','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.개인_리스트_DB_Filter 
	# disable authentication https://stackoverflow.com/questions/27085219/how-can-i-disable-authentication-in-django-rest-framework
	permission_classes = [개인_리스트_DB_전사_Permission]
	
	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		# for  day in day_list :
		#     if  not queryset.filter( 일자 = day)  : 
		#         is_Create = True
		#         개인_리스트_DB.objects.create (pk = None, 일자=day,
		#                                   등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
		#                                   조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
		
		# return 개인_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		return  queryset if not is_Create else 개인_리스트_DB.objects.exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')


class DB_Field_개인_리스트_DB_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = 개인_리스트_DB
	authentication_classes = []
	permission_classes = []

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.개인_리스트_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			#### 업무 보고용으로 추가됨
			'일자_3일' : get_3days(),
			####
			'table_header' :TABLE_HEADER_개인LIST,
			'no_Edit_cols' :['id', '조직이름_id', '일자',],
			'hidden_columns' :['id','조직이름_id'],
			'no_vContextMenuCols' :TABLE_HEADER_개인LIST,	### vContext menu를 생성하지 않는 col.
			'cols_width'  : COLS_WIDTH_개인LIST ,
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
				'공지내용_수정': {
					"position": (
						['공지내용'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "공지내용_수정",
					"tooltip" :"공지내용_수정",
					"objectName" : '공지내용_수정',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )


class DB_Field_개인_리스트_DB_이력조회_View(DB_Field_개인_리스트_DB_View):
	""" DB_Field_개인_리스트_DB_View 를 상속받아, table만 no-menu, no_edit 로 config 설정"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.res_dict = {
			'fields_model' : self.model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				####
				'table_header' : TABLE_HEADER_개인LIST,
				'no_Edit_cols' : TABLE_HEADER_개인LIST,
				'hidden_columns' :['id','조직이름_id'],
				'no_vContextMenuCols' : TABLE_HEADER_개인LIST,	### vContext menu를 생성하지 않는 col.
				'no_hContextMenus' : ['all'],  ### 'all' 또는 해당 rowNo
				'cols_width'  : COLS_WIDTH_개인LIST ,
				# 'v_Menus' : {
				#     'section':'',
				#     'Export_to_Excel': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				#         "title": "Export_to_excel",
				#         "tooltip" :"Excel로 table을 저장합니다.",
				#         "objectName" : 'Export_to_excel',
				#         "enabled" : True,
				#     },			
				#     'seperator':'',
				# },
				# 'h_Menus' : {
				#     'section':'',
				#     'seperator':'',
				#     'New': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "New",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'New_row',
				#         "enabled" : True,
				#     },
				#     'Delete': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "Delete",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'Delete_row',
				#         "enabled" : True,
				#     },
				# },
				'cell_Menus':{},                
			},
		}


class DB_Field_개인_리스트_DB_이력조회_전사_View(DB_Field_개인_리스트_DB_View):
	""" DB_Field_개인_리스트_DB_View 를 상속받아, table만 no-menu, no_edit 로 config 설정"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.res_dict = {
			'fields_model' : self.model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				####
				'table_header' : TABLE_HEADER_개인_보고용,
				'no_Edit_cols' : TABLE_HEADER_개인_보고용,
				'hidden_columns' :['id',],
				'no_vContextMenuCols' : TABLE_HEADER_개인_보고용,	### vContext menu를 생성하지 않는 col.
				'no_hContextMenus' : ['all'],  ### 'all' 또는 해당 rowNo
				'cols_width'  : COLS_WIDTH_개인LIST ,
				# 'v_Menus' : {
				#     'section':'',
				#     'Export_to_Excel': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				#         "title": "Export_to_excel",
				#         "tooltip" :"Excel로 table을 저장합니다.",
				#         "objectName" : 'Export_to_excel',
				#         "enabled" : True,
				#     },			
				#     'seperator':'',
				# },
				# 'h_Menus' : {
				#     'section':'',
				#     'seperator':'',
				#     'New': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "New",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'New_row',
				#         "enabled" : True,
				#     },
				#     'Delete': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "Delete",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'Delete_row',
				#         "enabled" : True,
				#     },
				# },
				'cell_Menus':{},                
			},
		}


class 개인_리스트_DB_개인_ViewSet(viewsets.ModelViewSet):
	""" 개인_리스트_DB view set for 3일"""    
	qs = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	serializer_class = serializers.개인_리스트_DB_Serializer 
	permission_classes = [개인_리스트_DB_개인_Permission]


	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		for  day in day_list :
			일자qs = queryset.filter( 일자 = day) 
			if  not 일자qs : 
				is_Create = True
				개인_리스트_DB.objects.create (pk = None, 일자=day,
										  등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
										  조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
			elif 일자qs.count() > 1:
				for _instance in 일자qs:
					if not len(_instance.업무내용 ) : _instance.delete()
		# return 개인_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		return  queryset if not is_Create else 개인_리스트_DB.objects.filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	

class 개인_리스트_DB_전사_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
	""" 개인_리스트_DB view set for 조회"""    
	queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	serializer_class = serializers.개인_리스트_DB_Serializer 
	permission_classes = [개인_리스트_DB_전사_Permission]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['업무내용', '주요산출물','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.개인_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.queryset.order_by('-일자')
		return queryset        
	

class 개인_리스트_DB_개인_조회_ViewSet(개인_리스트_DB_전사_조회_ViewSet):
	""" 개인_리스트_DB view set for 조회"""    
	permission_classes = []
	# permission_classes = [개인_리스트_DB_개인_Permission]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['업무내용', '주요산출물','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.개인_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.queryset.order_by('-일자')
		queryset = self.queryset.filter(등록자_id__user_fk=self.request.user.id).order_by('-일자')
		return queryset


class DB_Field_조직_리스트_DB_개인_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = ISSUE_리스트_DB
	authentication_classes = []
	permission_classes = []

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.조직_리스트_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	res_dict = {
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {},
		'fields_delete' : {},
		'table_config' : {
			#### 업무 보고용으로 추가됨
			'일자_3일' : get_3days(),
			####
			'table_header' : TABLE_HEADER_조직LIST,
			'no_Edit_cols' :['id', '조직이름_id', '일자',],
			'hidden_columns' :['id','조직이름_id'],
			'no_vContextMenuCols' : TABLE_HEADER_조직LIST,	### vContext menu를 생성하지 않는 col.
			'cols_width' : COLS_WIDTH_조직LIST,
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
				'공지내용_수정': {
					"position": (
						['공지내용'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "공지내용_수정",
					"tooltip" :"공지내용_수정",
					"objectName" : '공지내용_수정',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )

class DB_Field_조직_리스트_DB_이력조회_전사_View(DB_Field_조직_리스트_DB_개인_View):
	""" DB_Field_개인_리스트_DB_View 를 상속받아, table만 no-menu, no_edit 로 config 설정"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.res_dict = {
			'fields_model' : self.model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				####
				'table_header' : TABLE_HEADER_조직_보고용,
				'no_Edit_cols' : TABLE_HEADER_조직_보고용,
				'hidden_columns' :['id',],
				'no_vContextMenuCols' : TABLE_HEADER_조직_보고용,	### vContext menu를 생성하지 않는 col.
				'no_hContextMenus' : ['all'],  ### 'all' 또는 해당 rowNo
				'cols_width' : COLS_WIDTH_조직LIST,
				# 'v_Menus' : {
				#     'section':'',
				#     'Export_to_Excel': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				#         "title": "Export_to_excel",
				#         "tooltip" :"Excel로 table을 저장합니다.",
				#         "objectName" : 'Export_to_excel',
				#         "enabled" : True,
				#     },			
				#     'seperator':'',
				# },
				# 'h_Menus' : {
				#     'section':'',
				#     'seperator':'',
				#     'New': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "New",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'New_row',
				#         "enabled" : True,
				#     },
				#     'Delete': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "Delete",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'Delete_row',
				#         "enabled" : True,
				#     },
				# },
				'cell_Menus':{},                
			},
		}


class DB_Field_조직_리스트_DB_이력조회_View(DB_Field_조직_리스트_DB_개인_View):
	""" DB_Field_개인_리스트_DB_View 를 상속받아, table만 no-menu, no_edit 로 config 설정"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.res_dict = {
			'fields_model' : self.model_field,
			# 'fields_serializer' : serializer_field,
			'fields_append' : {},
			'fields_delete' : {},
			'table_config' : {
				####
				'table_header' : TABLE_HEADER_조직_보고용,
				'no_Edit_cols' : TABLE_HEADER_조직_보고용,
				'hidden_columns' :['id','조직'],
				'no_vContextMenuCols' : TABLE_HEADER_조직_보고용,	### vContext menu를 생성하지 않는 col.
				'no_hContextMenus' : ['all'],  ### 'all' 또는 해당 rowNo
				'cols_width' : COLS_WIDTH_조직LIST,
				# 'v_Menus' : {
				#     'section':'',
				#     'Export_to_Excel': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
				#         "title": "Export_to_excel",
				#         "tooltip" :"Excel로 table을 저장합니다.",
				#         "objectName" : 'Export_to_excel',
				#         "enabled" : True,
				#     },			
				#     'seperator':'',
				# },
				# 'h_Menus' : {
				#     'section':'',
				#     'seperator':'',
				#     'New': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "New",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'New_row',
				#         "enabled" : True,
				#     },
				#     'Delete': {
				#         "icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
				#         "title": "Delete",
				#         "tooltip" :"신규 작성합니다",
				#         "objectName" : 'Delete_row',
				#         "enabled" : True,
				#     },
				# },
				'cell_Menus':{},                
			},
		}


class 조직_리스트_DB_전사_ViewSet(viewsets.ModelViewSet):
	""" 조직_리스트_DB view set for 3일"""    
	qs = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','일자','등록자_id__보고순서')
	serializer_class = serializers.조직_리스트_DB_Serializer 
	# disable authentication https://stackoverflow.com/questions/27085219/how-can-i-disable-authentication-in-django-rest-framework
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['활동현황', '세부내용','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.조직_리스트_DB_Filter 
	permission_classes = [조직_리스트_DB_전사_Permission]
	
	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		return ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').exclude(등록자_id__user_fk__user_성명 ='admin').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','일자','등록자_id__보고순서')


class 조직_리스트_DB_개인_ViewSet(viewsets.ModelViewSet):
	""" 조직_리스트_DB view set for 3일"""    
	qs = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	serializer_class = serializers.조직_리스트_DB_Serializer 
	permission_classes = [조직_리스트_DB_개인_Permission]

	def get_queryset(self):
		day_list = get_3days()
		is_Create = False
		queryset = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		for  day in day_list :
			if  not queryset.filter( 일자 = day)  : 
				is_Create = True
				ISSUE_리스트_DB.objects.create (pk = None, 일자=day,
										  등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
										  조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
		
		# return ISSUE_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
		return  queryset if not is_Create else ISSUE_리스트_DB.objects.filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')

class 조직_리스트_DB_전사_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
	""" 개인_리스트_DB view set for 조회"""    
	queryset = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	serializer_class = serializers.조직_리스트_DB_Serializer
	permission_classes = [조직_리스트_DB_전사_Permission]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['활동현황', '세부내용','비고','조직이름_id__조직이름'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.조직_리스트_DB_Filter 

	def get_queryset(self):
		queryset = self.queryset.order_by('-일자');
		return queryset

class 조직_리스트_DB_개인_조회_ViewSet(조직_리스트_DB_전사_조회_ViewSet):
	""" 개인_리스트_DB view set for 조회"""    

	def get_queryset(self):
		queryset = self.queryset.filter(등록자_id__user_fk=self.request.user.id).order_by('-일자')
		return queryset



class 전기사용량_ViewSet(viewsets.ModelViewSet):
	MODEL = 전기사용량_DB
	queryset = 전기사용량_DB.objects.order_by('-일자')
	serializer_class = serializers.전기사용량_DB_Serializer 
	permission_classes = [전기사용량_DB_Permission]

	parser_classes = [MultiPartParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# search_fields =['활동현황', '세부내용','비고'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.전기사용량_DB_Filter

	def get_queryset(self):
		return self.MODEL.objects.order_by('-일자')
	


	# def get_queryset(self):
	#     day_list = get_3days()
	#     is_Create = False
	#     # print ( day_list)
	#     queryset = 전기사용량_DB.objects.filter(일자__in=day_list).order_by('-일자')
	#     for  day in day_list[1:] :   #최근 순으로 됨
	#         if  not queryset.filter( 일자 = day)  : 
	#             전기사용량_DB.objects.create ( 일자=day, 등록자 = 'admin' )

	#     return  전기사용량_DB.objects.filter(일자__gte= _get_1Month()).order_by('-일자')
	


class 휴일등록_DB_개인_ViewSet(viewsets.ModelViewSet):
	MODEL = 휴일_DB
	queryset = 휴일_DB.objects.all()
	serializer_class = serializers.휴일등록_DB__Serializer
	permission_classes = [휴일등록_DB_Permission]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
	]
	# search_fields =['활동현황', '세부내용','비고'] # 👈 filters에 SearchFilter 지정
	filterset_class =  customfilters.휴일_DB_Filter

	cache_key = '일일보고_휴일등록_LIST'  # 캐시 키
	cache_time = 60*60*12  # 캐시 유지 시간 (초)
	
	def get_queryset(self):       
		# 중복된 휴일 찾기
		# duplicates = 휴일_DB.objects.values('휴일').annotate(count=Count('id')).filter(count__gt=1)
		# # 각 중복 항목에 대해 하나만 남기고 삭제
		# for dup in duplicates:
		# 	records = 휴일_DB.objects.filter(휴일=dup['휴일']).order_by('id')
		# 	# 첫 번째 레코드의 ID 가져오기
		# 	first_record_id = records.first().id
		# 	# 첫 번째 레코드를 제외한 나머지 삭제
		# 	휴일_DB.objects.filter(휴일=dup['휴일']).exclude(id=first_record_id).delete()	
		# queryset = self.MODEL.objects.order_by('-휴일')
		# cache.set(self.cache_key, queryset, self.cache_time)
		# return self.MODEL.objects.order_by('-휴일')

		queryset = cache.get(self.cache_key)
		
		if queryset is None:
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = self.MODEL.objects.order_by('-휴일')
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset
	
