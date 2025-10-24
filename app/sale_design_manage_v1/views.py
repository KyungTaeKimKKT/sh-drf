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
from . import customfilters

from .models import (
	디자인의뢰,
	의뢰file,
	완료file,
	Group의뢰
)
from users.models import Api_App권한

import util.utils_func as Util
import copy 


### CONST
TABLE_HEADER_의뢰 =['id', '고객사','구분','의뢰여부','의뢰차수','현장명','el수량','운행층수','상세내용','영업담당자','의뢰파일수', '샘플의뢰여부','비고','의뢰일','완료요청일', ]
TABLE_HEADER_접수 = TABLE_HEADER_의뢰 + ['접수디자이너','접수여부','접수일']
TABLE_HEADER_완료 = TABLE_HEADER_접수 + ['완료파일수', '완료디자이너', '완료여부', '완료일', ]

TABLE_HEADER_이력조회 = TABLE_HEADER_완료
TABLE_HEADER_관리 = TABLE_HEADER_완료

#####

class 의뢰file_ViewSet(viewsets.ModelViewSet):
	""" 디자인관리 의뢰file view set """    
	MODEL = 의뢰file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.의뢰file_Serializer 
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]

class 완료file_ViewSet(viewsets.ModelViewSet):
	""" 디자인관리 완료file view set """    
	MODEL = 완료file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.완료file_Serializer 
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]


class DB_정리_의뢰차수(APIView):
	authentication_classes = []
	permission_classes = []

	def post(self, request, format=None):
		qs = 디자인의뢰.objects.order_by('현장명', '-의뢰차수')

		현장명List = qs.values_list( '현장명', flat=True).distinct('현장명')

		틀림list = []
		for _instance in qs:
			_instance.의뢰일 = _instance.등록일
			_instance.save()

		return Response(틀림list)
	

class DB_Field_디자인관리_View(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""

	MODEL = 디자인의뢰
	authentication_classes = []
	permission_classes = []

	model_field = Util.get_MODEL_field_type(MODEL)

	_serializer = serializers.디자인의뢰_DB_Serializer()
	serializer_field = Util.get_Serializer_field_type(_serializer)

	__table_header = TABLE_HEADER_관리

	접수디자이너list = []		###😀 아래가 makemigrations 시, error 발생???
	user_pks = [] #Api_App권한.objects.filter(div='디자인관리', name='완료')[0].user_pks.all()
	접수디자이너list = [] #[ user.id  for user in user_pks if user.id != 1 ]


	
	res_dict = {
		###😀추가된 부분
		'URL_의뢰file_fks' : '디자인관리/의뢰file-viewSet/',
		'URL_완료file_fks' : '디자인관리/완료file-viewSet/',
		'구분list' : ['NE','MOD','개발','기타'],
		'고객사list' : ['현대EL','OTIS','TKE','미정'],
		###################################
		'fields_model' : model_field,
		# 'fields_serializer' : serializer_field,
		'fields_append' : {'의뢰파일수': 'Interger', '완료파일수':'Integer', },
		'fields_delete' : {},
		'table_config' : {
			###😀추가된 부분
			'구분list' : ['NE','MOD','개발','기타'],
			'고객사list' : ['현대EL','OTIS','TKE','미정'],
			'접수디자이너list': 접수디자이너list,
			'cols_width' : {
				'현장명'  : 16*30,
				'상세내용' : 16*30,
				'비고'     : 16*25,
			},

			#############
			'table_header' :__table_header,
			'no_Edit_cols' :['id','의뢰일','의뢰파일수','영업담당자','완료파일수','의뢰차수'],
			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
			'cell_menus_cols' :['현장명', '의뢰파일수', '완료파일수'],
			'cell_menus_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.yellow ))",
			'hidden_columns' :[],
			'no_vContextMenuCols' :__table_header, ### vContext menu를 생성하지 않는 col.
			'no_hContextMenuRows' :[],
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
					"tooltip" :"db에서 삭제합니다",
					"objectName" : 'Delete_row',
					"enabled" : True,
				},
			},
			'cell_Menus':{
				'section':'',
				'seperator':'',
				'파일_업로드': {
					"position": (
						['의뢰파일수','완료파일수'],	### table_header name
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
						['의뢰파일수','완료파일수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 다운로드",
					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
					"objectName" : '파일_다운로드',
					"enabled" : True,
				},
				'파일_View': {
					"position": (
						['의뢰파일수','완료파일수'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "파일 View",
					"tooltip" :"등록된 파일을 View 할 수 있습니다.",
					"objectName" : 'file_viewer',
					"enabled" : True,
				},
				'seperator':'',
				'현장명_검색': {
					"position": (
						['현장명'],	### table_header name
						['all']		### 전체 경우, 'all' 아니면 rowNo
					),
					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
					"title": "현장명_검색",
					"tooltip" :"현장명을 검색하영 관련 정보를 가져옵니다.",
					"objectName" : '현장명_검색',
					"enabled" : True,
				},
			}
		},

	}

	def get(self, request, format=None):
		return Response ( self.res_dict )
	
	# def _init_res_dict(self):
	# 	res_dict = {
	# 		###😀추가된 부분
	# 		'URL_의뢰file_fks' : '디자인관리/의뢰file-viewSet/',
	# 		'URL_완료file_fks' : '디자인관리/완료file-viewSet/',
	# 		'구분list' : ['NE','MOD','개발','기타'],
	# 		'고객사list' : ['현대EL','OTIS','TKE','미정'],
	# 		###################################
	# 		'fields_model' : model_field,
	# 		# 'fields_serializer' : serializer_field,
	# 		'fields_append' : {'의뢰파일수': 'Interger', '완료파일수':'Integer', },
	# 		'fields_delete' : {},
	# 		'table_config' : {
	# 			###😀추가된 부분
	# 			'구분list' : ['NE','MOD','개발','기타'],
	# 			'고객사list' : ['현대EL','OTIS','TKE','미정'],
	# 			'접수디자이너list': 접수디자이너list,
	# 			'cols_width' : {
	# 				'현장명'  : 16*30,
	# 				'상세내용' : 16*30,
	# 				'비고'     : 16*25,
	# 			},

	# 			#############
	# 			'table_header' :__table_header,
	# 			'no_Edit_cols' :['id','의뢰일','의뢰파일수','영업담당자','완료파일수','의뢰차수'],
	# 			'no_Edit_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.darkGray ))",
	# 			'cell_menus_cols' :['현장명', '의뢰파일수', '완료파일수'],
	# 			'cell_menus_cols_color' : "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.yellow ))",
	# 			'hidden_columns' :[],
	# 			'no_vContextMenuCols' :__table_header, ### vContext menu를 생성하지 않는 col.
	# 			'no_hContextMenuRows' :[],
	# 			'v_Menus' : {
	# 				'section':'',
	# 				'Export_to_Excel': {
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-export_to_excel')",
	# 					"title": "Export_to_excel",
	# 					"tooltip" :"Excel로 table을 저장합니다.",
	# 					"objectName" : 'Export_to_excel',
	# 					"enabled" : True,
	# 				},			
	# 				'seperator':'',
	# 			},
	# 			'h_Menus' : {
	# 				'section':'',
	# 				'seperator':'',
	# 				'New': {
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "New",
	# 					"tooltip" :"신규 작성합니다",
	# 					"objectName" : 'New_row',
	# 					"enabled" : True,
	# 				},
	# 				'Delete': {
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "Delete",
	# 					"tooltip" :"db에서 삭제합니다",
	# 					"objectName" : 'Delete_row',
	# 					"enabled" : True,
	# 				},
	# 			},
	# 			'cell_Menus':{
	# 				'section':'',
	# 				'seperator':'',
	# 				'파일_업로드': {
	# 					"position": (
	# 						['의뢰파일수','완료파일수'],	### table_header name
	# 						['all']		### 전체 경우, 'all' 아니면 rowNo
	# 					),
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "파일 업로드",
	# 					"tooltip" :"파일 업로드",
	# 					"objectName" : '파일_업로드',
	# 					"enabled" : True,
	# 				},
	# 				'seperator':'',
	# 				'파일_다운로드': {
	# 					"position": (
	# 						['의뢰파일수','완료파일수'],	### table_header name
	# 						['all']		### 전체 경우, 'all' 아니면 rowNo
	# 					),
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "파일 다운로드",
	# 					"tooltip" :"등록된 파일을 다운로드 할 수 있습니다.",
	# 					"objectName" : '파일_다운로드',
	# 					"enabled" : True,
	# 				},
	# 				'파일_View': {
	# 					"position": (
	# 						['의뢰파일수','완료파일수'],	### table_header name
	# 						['all']		### 전체 경우, 'all' 아니면 rowNo
	# 					),
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "파일 View",
	# 					"tooltip" :"등록된 파일을 View 할 수 있습니다.",
	# 					"objectName" : 'file_viewer',
	# 					"enabled" : True,
	# 				},
	# 				'seperator':'',
	# 				'현장명_검색': {
	# 					"position": (
	# 						['현장명'],	### table_header name
	# 						['all']		### 전체 경우, 'all' 아니면 rowNo
	# 					),
	# 					"icon" : "QtGui.QIcon(':/table-icons/tb-insert_row')",
	# 					"title": "현장명_검색",
	# 					"tooltip" :"현장명을 검색하영 관련 정보를 가져옵니다.",
	# 					"objectName" : '현장명_검색',
	# 					"enabled" : True,
	# 				},
	# 			}
	# 		},

	# 	}
	# 	self.res_dict['접수디자이너list'] = self._get_접수디자이너list()

	# def _get_접수디자이너list(self):
	# 	user_pks = Api_App권한.objects.filter(div='디자인관리', name='완료')[0].user_pks.all()
	# 	return [ user.id  for user in user_pks if user.id != 1 ]

class DB_Field_디자인의뢰_View(DB_Field_디자인관리_View):
	""" DB FILED VIEW {NAME:TYPE}"""

	res_dict = copy.deepcopy(DB_Field_디자인관리_View.res_dict)
	__table_header = TABLE_HEADER_의뢰
	res_dict['table_config']['table_header'] = __table_header

class DB_Field_디자인재의뢰_View(DB_Field_디자인관리_View):
	""" DB FILED VIEW {NAME:TYPE}"""

	res_dict = copy.deepcopy(DB_Field_디자인관리_View.res_dict)
	__table_header = TABLE_HEADER_의뢰
	res_dict['table_config']['table_header'] = __table_header
	del res_dict['table_config']['h_Menus']['New']

class DB_Field_디자인접수_View(DB_Field_디자인관리_View):
	""" DB FILED VIEW {NAME:TYPE}"""

	res_dict = copy.deepcopy(DB_Field_디자인관리_View.res_dict)
	__table_header = TABLE_HEADER_접수
	res_dict['table_config']['table_header'] = __table_header
	res_dict['table_config']['no_Edit_cols'] = TABLE_HEADER_의뢰+['접수일']

class DB_Field_디자인완료_View(DB_Field_디자인관리_View):
	""" DB FILED VIEW {NAME:TYPE}"""

	res_dict = copy.deepcopy(DB_Field_디자인관리_View.res_dict)
	__table_header =TABLE_HEADER_완료					
	res_dict['table_config']['table_header'] = __table_header
	res_dict['table_config']['no_Edit_cols'] = TABLE_HEADER_접수+['완료일','완료디자이너']


class DB_Field_이력조회_View(DB_Field_디자인관리_View):
	""" DB FILED VIEW {NAME:TYPE}"""

	res_dict = copy.deepcopy(DB_Field_디자인관리_View.res_dict)
	__table_header = TABLE_HEADER_이력조회
					
	res_dict['table_config']['table_header'] = __table_header
	res_dict['table_config']['no_Edit_cols'] = __table_header
	res_dict['table_config']['no_Edit_cols_color'] = "QtCore.QVariant( QtGui.QColor( QtCore.Qt.GlobalColor.white ))"

	res_dict['table_config']['h_Menus'] = {}
	del res_dict['table_config']['cell_Menus']['파일_업로드']



class 디자인관리_ViewSet(viewsets.ModelViewSet):
	""" 디자인관리 관리자용 view set """    
	MODEL = 디자인의뢰
	qs = MODEL.objects.order_by('-id')
	serializer_class = serializers.디자인의뢰_DB_Serializer 
	parser_classes = [MultiPartParser,FormParser]
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	filterset_class = customfilters.디자인의뢰_DB_FilterSet

	def get_queryset(self):     
		# for _instance in self.qs:
		# 	if not _instance.의뢰일  or not _instance.의뢰여부:
		# 		_instance.의뢰일 = _instance.등록일
		# 		_instance.의뢰여부 = True
		# 		_instance.save()  
		return self.MODEL.objects.order_by('-의뢰일')


class 디자인관리_의뢰_ViewSet(디자인관리_ViewSet):
	qs = 디자인의뢰.objects.order_by('-의뢰일')

	def get_queryset(self):       
		qs = 디자인의뢰.objects.exclude(의뢰여부=True).filter(sales_user_fk = self.request.user).order_by('-의뢰일')
		return qs
		# return qs
		# if qs.count():
		# 	return qs
		# else :
		# 	self.MODEL.objects.create( sales_user_fk = self.request.user, 영업담당자=self.request.user.user_성명)
		# 	qs = 디자인의뢰.objects.exclude(의뢰여부=True).filter(sales_user_fk = self.request.user).order_by('-의뢰일')
		# 	return qs
	
	def create(self, request, *args, **kwargs):
		""" create에서 정리할 것"""
		# return super().create( request, *args, **kwargs )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['영업담당자'] = request.user.user_성명
			request.data['sales_user_fk'] = request.user.id
			request.data['의뢰여부'] = False
			request.data['의뢰차수'] = 1
			request.data['완료요청일'] = datetime.now() + timedelta(days=3)

		return super().create( request, *args, **kwargs )


	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			# request.data['영업담당자'] = request.user.user_성명
			if request.data.get('의뢰차수', False) : request.data['의뢰차수'] = 1
			if request.data.get('의뢰여부', False) : request.data['의뢰일'] = datetime.now()
		return super().update(request, *args, **kwargs)
	
	
class 디자인관리_재의뢰_ViewSet(디자인관리_ViewSet):
	qs = 디자인의뢰.objects.order_by('-의뢰일')
	def get_queryset(self):       
		return 디자인의뢰.objects.exclude(의뢰여부=True).filter(sales_user_fk = self.request.user,  의뢰차수__gte = 2).order_by('-의뢰일')
	
	def create(self, request, *args, **kwargs):
		""" 재의뢰는 기존을 것을 copy 하여 생성하므로,  create에서 정리할 것"""
		# return super().create( request, *args, **kwargs )
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			request.data['영업담당자'] = request.user.user_성명
			request.data['sales_user_fk'] = request.user.id
			request.data['의뢰일'] = datetime.now()
			request.data['완료요청일'] = datetime.now() + timedelta(days=3)
			print ( self, request.data )
		return super().create( request, *args, **kwargs )

	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if request.data.get('의뢰여부', False) : request.data['의뢰일'] = datetime.now()
		return super().update(request, *args, **kwargs)
		
	
class 디자인관리_접수_ViewSet(디자인관리_ViewSet):
	qs = 디자인의뢰.objects.order_by('-의뢰일')

	def get_queryset(self):       
		return 디자인의뢰.objects.exclude(접수여부=True).filter(의뢰여부=True).order_by('-의뢰일')
	
	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if request.data.get('접수여부', False)  :
				request.data['접수일'] = datetime.now()
				# request.data['완료디자이너'] = request.user.user_성명
		return super().update(request, *args, **kwargs)

	
class 디자인관리_완료_ViewSet(디자인관리_ViewSet):
	qs = 디자인의뢰.objects.order_by('-의뢰일')
	def get_queryset(self):       
		return 디자인의뢰.objects.exclude(완료여부=True).filter(designer_fk= self.request.user, 접수여부=True).order_by('-의뢰일')
	
	def update(self, request, *args, **kwargs):
		if isinstance(request.data, QueryDict):  # optional
			request.data._mutable = True
			if request.data.get('완료여부', False)  :
				request.data['완료일'] = datetime.now()
				request.data['완료디자이너'] = request.user.user_성명
		return super().update(request, *args, **kwargs)
	

class 디자인관리_이력조회_ViewSet(디자인관리_ViewSet, viewsets.ReadOnlyModelViewSet):
	def get_queryset(self):       
		return 디자인의뢰.objects.filter(의뢰여부=True).order_by('-의뢰일')

	
class Group의뢰_ViewSet(viewsets.ModelViewSet):
	qs = Group의뢰.objects.order_by('-id')
	serializer_class = serializers.Group의뢰_Serializer 
	# filter_backends = [
	#        SearchFilter, 
	#        filters.DjangoFilterBackend,
	#     ]
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = 디자인관리_Pagination

	def get_queryset(self):       
		return Group의뢰.objects.order_by('-id')

class dashBoard_ViewSet(APIView):

	관리자list = ['admin','김경태','김동주']
	authentication_classes = []
	permission_classes = []

	def get(self, request, format=None):
		qs = 디자인의뢰.objects.filter(의뢰여부=True).order_by('-의뢰일')
		allModelFields = [field.name for field in 디자인의뢰._meta.get_fields()]
		transferFields  = allModelFields.copy()
		transferFields[:] = (value for value in allModelFields if  value not in [] ) # '상세내용','비고'
		# serialQS = serializers.serialize("json", 디자인의뢰.objects.filter(등록일__lte=timezone.now()).order_by('-등록일'), fields=transferFields )

		등록자_DB = list(Api_App권한.objects.filter(url__contains = '/디자인관리/디자인관리_의뢰.html').values_list('user_pks__user_성명',flat=True))
		new_등록자_DB = [name for name in 등록자_DB if name not in self.관리자list]

		today = date.today()
		start_date = today - timedelta(days=today.weekday())
		end_date = start_date + timedelta(days=6)
		df = pd.DataFrame( list( qs
								.filter( 의뢰일__range=(start_date, end_date) ) 
								.values_list('고객사')    ) )
		if len(df.index) and len(df.columns):
			df2 = df.set_axis( ['customer'], axis=1 )
			df2['count'] = 1
			pvTable = pd.pivot_table(df2,  index='customer', values='count', aggfunc='sum') 
			등록현황toList = [['고객사'] + pvTable.columns.tolist()] + pvTable.reset_index().values.tolist()
		else: 등록현황toList =[]

		df = pd.DataFrame( list( qs
								.filter( 접수일__range=(start_date, end_date)) 
								.values_list('고객사', '영업담당자' ))    )
		if len(df.index) and len(df.columns):
			df2 = df.set_axis( ['customer', 'person'], axis=1 )
			pvTable = pd.pivot_table(df2,  index='person', columns='customer', aggfunc=len, fill_value=0)
			접수현황toList = [['등록자'] + pvTable.columns.tolist()] + pvTable.reset_index().values.tolist()
		else: 접수현황toList =[]

		df = pd.DataFrame( list( qs
								.filter( 접수일__range=(start_date, end_date)  ) 
								.values_list('완료여부', '접수디자이너' ))    )
		if len(df.index) and len(df.columns):
			df2 = df.set_axis( ['완료여부', '접수디자이너'], axis=1 )
			pvTable = pd.pivot_table(df2,  index='접수디자이너', columns='완료여부', aggfunc=len, fill_value=0)

			if ( len( pvTable.columns.to_list() )  != 2 ):
				for idx, col in enumerate(pvTable.columns):
					if (idx == 0 & col != 'false') : pvTable.insert (idx, '미완료', 0 )
					else: pvTable.insert (idx, '완료', 0 )
			pvTable = pvTable.set_axis( ['미완료','완료'], axis=1 )
			완료현황toList = [['접수디자이너'] + pvTable.columns.tolist()] + pvTable.reset_index().values.tolist()
		else: 완료현황toList =[]

		return Response( data={'등록현황':등록현황toList, '접수현황':접수현황toList,'완료현황':완료현황toList } , status=status.HTTP_200_OK )



# class 개인_리스트_DB_개인_ViewSet(viewsets.ModelViewSet):
#     """ 개인_리스트_DB view set for 3일"""    
#     qs = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.개인_리스트_DB_Serializer 
#     permission_classes = [개인_리스트_DB_개인_Permission]

#     def get_queryset(self):
#         day_list = get_3days()
#         is_Create = False
#         queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#         for  day in day_list :
#             if  not queryset.filter( 일자 = day)  : 
#                 is_Create = True
#                 개인_리스트_DB.objects.create (pk = None, 일자=day,
#                                           등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
#                                           조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
		
#         # return 개인_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#         return  queryset if not is_Create else 개인_리스트_DB.objects.filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
	

# class 개인_리스트_DB_개인_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     """ 개인_리스트_DB view set for 조회"""    
#     qs = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.개인_리스트_DB_Serializer 
#     permission_classes = [개인_리스트_DB_개인_Permission]
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['업무내용', '주요산출물','비고'] # 👈 filters에 SearchFilter 지정
#     filterset_class =  customfilters.개인_리스트_DB_Filter 


#     def get_queryset(self):
#         queryset = self.qs.filter(등록자_id__user_fk=self.request.user.id)
#         return queryset

# class 개인_리스트_DB_전사_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     """ 개인_리스트_DB view set for 조회"""    
#     queryset = 개인_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.개인_리스트_DB_Serializer 
#     permission_classes = [개인_리스트_DB_전사_Permission]
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['업무내용', '주요산출물','비고'] # 👈 filters에 SearchFilter 지정
#     filterset_class =  customfilters.개인_리스트_DB_Filter 

#     # def get_queryset(self):
#     #     queryset = self.qs.filter(등록자_id__user_fk=self.request.user.id)
#     #     return queryset        
	

# class 조직_리스트_DB_전사_ViewSet(viewsets.ModelViewSet):
#     """ 조직_리스트_DB view set for 3일"""    
#     qs = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','일자','등록자_id__보고순서')
#     serializer_class = serializers.조직_리스트_DB_Serializer 
#     # disable authentication https://stackoverflow.com/questions/27085219/how-can-i-disable-authentication-in-django-rest-framework
#     permission_classes = [조직_리스트_DB_전사_Permission]
	
#     def get_queryset(self):
#         return self.qs


# class 조직_리스트_DB_개인_ViewSet(viewsets.ModelViewSet):
#     """ 조직_리스트_DB view set for 3일"""    
#     qs = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(일자__in=get_3days()).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.조직_리스트_DB_Serializer 
#     permission_classes = [조직_리스트_DB_개인_Permission]

#     def get_queryset(self):
#         day_list = get_3days()
#         is_Create = False
#         queryset = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#         for  day in day_list :
#             if  not queryset.filter( 일자 = day)  : 
#                 is_Create = True
#                 ISSUE_리스트_DB.objects.create (pk = None, 일자=day,
#                                           등록자_id=개인_INFO.objects.get(user_fk=self.request.user.id ),
#                                           조직이름_id=조직_INFO.objects.get(조직이름=self.request.user.기본조직1)) ## 정상이면 foreingkey로 갔어야하는데...
		
#         # return ISSUE_리스트_DB.objects.filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#         return  queryset if not is_Create else ISSUE_리스트_DB.objects.filter(등록자_id__user_fk=self.request.user.id).filter(일자__in=day_list).order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')


# class 조직_리스트_DB_개인_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     """ 개인_리스트_DB view set for 조회"""    
#     qs = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.조직_리스트_DB_Serializer
#     permission_classes = [조직_리스트_DB_개인_Permission]
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['활동현황', '세부내용','비고'] # 👈 filters에 SearchFilter 지정
#     filterset_class =  customfilters.조직_리스트_DB_Filter 


#     def get_queryset(self):
#         queryset = self.qs.filter(등록자_id__user_fk=self.request.user.id)
#         return queryset

# class 조직_리스트_DB_전사_조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     """ 개인_리스트_DB view set for 조회"""    
#     queryset = ISSUE_리스트_DB.objects.select_related('조직이름_id','등록자_id').order_by('조직이름_id__보고순서','등록자_id__보고순서','일자')
#     serializer_class = serializers.조직_리스트_DB_Serializer
#     permission_classes = [조직_리스트_DB_전사_Permission]
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['활동현황', '세부내용','비고'] # 👈 filters에 SearchFilter 지정
#     filterset_class =  customfilters.조직_리스트_DB_Filter 


#     # def get_queryset(self):
#     #     queryset = self.qs.filter(등록자_id__user_fk=self.request.user.id)
#     #     return queryset

# class 전기사용량_ViewSet(viewsets.ModelViewSet):
#     queryset = 전기사용량_DB.objects.filter(일자__gte= _get_1Month()).order_by('-일자')
#     serializer_class = serializers.전기사용량_DB_Serializer 
#     permission_classes = [전기사용량_DB_Permission]

#     parser_classes = [MultiPartParser]
