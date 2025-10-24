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

from util.utils_viewset import Util_Model_Viewset
# from rest_framework.pagination import PageNumberPagination

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
import json

from django.db.models import Q

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )
from . import serializers
from util.customfilters import 생산지시_DB_FilterSet

from .models import (
	도면file, 
	도면상세내용, 
	도면정보,
	Process,
	생산지시,
	SPG,
	SPG_Table,
	SPG_file,
	TAB_Made_file,
	JAMB_file,
	JAMB_발주정보,
	Group생산지시,
	# 결재내용,
)

class 도면정보_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  도면정보
	queryset =  MODEL.objects.order_by('-id')   
	serializer_class = serializers.도면정보_Serializer  

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')
   
 
class HTM_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  Process
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.Process_Serializer

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')

class SPG_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  SPG_Table
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_Table_Serializer

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')


class SPG_File_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = SPG_file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')
	
class  TAB_Made_file_Viewset(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = TAB_Made_file
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers. TAB_Made_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')

class 생산지시_fields_List(APIView):

	def get(self, request, format=None):
		"""
		Return a list of all 생산지시 fileds.
		"""
		fields = [f.name for f in 생산지시._meta.fields] + ['process_fks']
		fields_obj = { f:'' for f in fields}
		
		fields_obj['id'] = 'new'
		return Response(fields_obj)
	
class SPG_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	""" SPG 관리장용 view set """
	MODEL = SPG
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')
	
	# https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) )

		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def update(self, request, *args, **kwargs):
		serializer = self.get_serializer(instance=self.get_object(),
										 data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) ,
										 partial=True
										 )

		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)

	
	def _get_kwarg_for_serializer(self, request) -> dict:
		data = request.data
		files = request.FILES
		self.fks_ids = {
			"spg_table_fks" : SPG_Table,
		}
		result = {}
		for fks_name  in self.fks_ids:
			if (fks:=data.get(fks_name) ):
				result.update ( { fks_name : json.loads( fks )})

		return result
	


class 생산지시_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	""" 생산지시 관리자용 view set """    
	MOEL = 생산지시
	queryset = MOEL.objects.order_by('-id')
	serializer_class = serializers.생산지시_Serializer 

	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	filterset_class =  생산지시_DB_FilterSet
	

	def get_queryset(self):       
		return self.MOEL.objects.order_by('-id')
	
	# https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
	def create(self, request, *args, **kwargs):
		print (' view create내 ', request.data)
		serializer = self.get_serializer(data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) )

		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def update(self, request, *args, **kwargs):
		print ( 'view: update \n', request.data)
		serializer = self.get_serializer(instance=self.get_object(),
										 data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) ,
										partial=True)

		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)

	
	def _get_kwarg_for_serializer(self, request) -> dict:
		data = request.data
		files = request.FILES

		self.fks_ids = {
			"spg_fks" : SPG,
			"tab_made_fks" : TAB_Made_file,
			"도면정보_fks" : 도면정보,
			"process_fks" : Process,
		}
		result = {}
		for fks_name  in self.fks_ids:
			if (fks:=data.get(fks_name) ):
				result.update ( { fks_name : json.loads( fks )})
		return result
		# result = {
		# 	# '품질비용_fk' : json.loads( 품질비용_fk ) if (품질비용_fk:=data.get('품질비용_fk')) else {},
		# 	'process_fks' : json.loads( process_fks ) if (process_fks:= data.get('process_fks') ) else [],
		# 	'도면정보_fks' : json.loads( 도면정보_fks ) if (도면정보_fks:= data.get('도면정보_fks') ) else [],
		# 	'spg_fks' :json.loads( spg_fks ) if (spg_fks:= data.get('spg_fks') ) else [],
		# 	'tab_made_fks' :json.loads( tab_made_fks ) if (tab_made_fks:= data.get('tab_made_fks') ) else [],
		# 	# '첨부file_fks_삭제' :  첨부file_fks_삭제 if (첨부file_fks_삭제 := data.get('첨부file_fks_삭제')) else False,
		# 	# '첨부file_fks' : 첨부file_fks if  (첨부file_fks:=files.getlist('첨부file_fks')) else [],
		# 	# '첨부file_fks_json' : json.loads( 첨부file_fks_json ) if  (첨부file_fks_json:=data.get('첨부file_fks_json',[] ) ) else [],

		# 	# '완료file_fks' : 완료file_fks if  (완료file_fks:=files.getlist('완료file_fks')) else [],
		#    }


	
	# def destroy(self, request, *args, **kwargs):
	#     _instance = self.get_object()

	#     for obj in _instance.process_fks.all():
	#         obj.delete()

	#     _instance.delete()
	#     return Response(status=status.HTTP_204_NO_CONTENT)

class JAMB_file_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = JAMB_file
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.JAMB_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')
	
class JAMB_발주정보_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = JAMB_발주정보
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.JAMB_발주정보_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')
	
		# https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
	def create(self, request, *args, **kwargs):
		print (' view create내 ', request.data)
		serializer = self.get_serializer(data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) )

		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def update(self, request, *args, **kwargs):
		serializer = self.get_serializer(instance=self.get_object(),
										 data=request.data, 
										 fks=self._get_kwarg_for_serializer(request) )

		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)


	def _get_kwarg_for_serializer(self, request) -> dict:
		data = request.data
		files = request.FILES
		result = {}
		fks_ids = ["JAMB_files_fks"]
		if fks_ids:
			for name in fks_ids:
				result.update( { name : json.loads( fks_ids ) if (fks_ids:= data.get(name) ) else []})
		# result = {
		#     # '품질비용_fk' : json.loads( 품질비용_fk ) if (품질비용_fk:=data.get('품질비용_fk')) else {},
		#     'process_fks' : json.loads( process_fks ) if (process_fks:= data.get('process_fks') ) else [],
		#     '도면정보_fks' : json.loads( 도면정보_fks ) if (도면정보_fks:= data.get('도면정보_fks') ) else [],
		#     'spg_fks' :json.loads( spg_fks ) if (spg_fks:= data.get('spg_fks') ) else [],
		#     'tab_made_fks' :json.loads( tab_made_fks ) if (tab_made_fks:= data.get('tab_made_fks') ) else [],
		#     # '첨부file_fks_삭제' :  첨부file_fks_삭제 if (첨부file_fks_삭제 := data.get('첨부file_fks_삭제')) else False,
		#     # '첨부file_fks' : 첨부file_fks if  (첨부file_fks:=files.getlist('첨부file_fks')) else [],
		#     # '첨부file_fks_json' : json.loads( 첨부file_fks_json ) if  (첨부file_fks_json:=data.get('첨부file_fks_json',[] ) ) else [],

		#     # '완료file_fks' : 완료file_fks if  (완료file_fks:=files.getlist('완료file_fks')) else [],
		#    }

		return result


class 생산지시_JAMB_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
	""" 생산지시 JAMB 관리자용 view set """    
	MODEL = 생산지시
	queryset = 생산지시.objects.order_by('-id')
	serializer_class = serializers.생산지시_Serializer 
	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	filterset_class =  생산지시_DB_FilterSet
	

	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')


class 생산지시_배포_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
	""" 생산지시 배포 """
	MODEL = 생산지시
	queryset = 생산지시.objects.order_by('-id')
	serializer_class = serializers.생산지시_Serializer 
	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	filterset_class =  생산지시_DB_FilterSet
	

	def get_queryset(self):       
		return self.MODEL.objects.filter(진행현황_htm='배포', 진행현황_jamb='배포').order_by('-id')

class 생산지시_배포_생산계획대기_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
	""" 생산지시 배포 """
	MODEL = 생산지시
	queryset = 생산지시.objects.order_by('-id')
	serializer_class = serializers.생산지시_Serializer 
	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	filterset_class =  생산지시_DB_FilterSet

	def get_queryset(self):       
		htm검색조건 = Q(진행현황_htm='배포') & ~Q(is_계획반영_htm =True) 
		jamb검색조건 = Q(진행현황_jamb='배포') & ~Q(is_계획반영_jamb =True) 
		queryset = self.MODEL.objects.filter( htm검색조건 | jamb검색조건).order_by('-id')		

		return queryset

# class 생산지시_결재_ViewSet (생산지시_ViewSet ):
#     serializer_class = serializers.생산지시_결재_Serializer 
   
#     def get_queryset(self):       
#         qs = 생산지시.objects.order_by('-id')
#         return qs.filter( 결재내용_fks__결재자 = self.request.user.id , 결재내용_fks__결재결과= None )
	
#     def update(self, request, *args, **kwargs):
#         # main thing starts
#         instance = self.get_object()
#         결재내용_fks = json.loads( request.data.get('결재내용_fks') ) if  request.data.get('결재내용_fks') else []

#         serializer = self.get_serializer(instance, data=request.data, 결재내용_fks=결재내용_fks, partial=True )
#         # main thing ends

#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         headers = self.get_success_headers(serializer.data)
#         # return Response({'status': 200})
#         return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)


# class 생산지시_진행현황_ViewSet (생산지시_ViewSet ):
   
#     def get_queryset(self):       
#         qs = 생산지시.objects.order_by('-id')
#         return qs.filter( 결재내용_fks__결재자 = self.request.user.id  )
	
	
# class 생산지시_배포_ViewSet (생산지시_ViewSet ):
   
#     # 진행현황은 model save  할때, method 로 status 계산해서 저장함
#     def get_queryset(self):       
#         qs = 생산지시.objects.order_by('-id')
#         return qs.filter(진행현황 = '완료')
 


# class 결재내용_ViewSet(viewsets.ModelViewSet):
#     queryset = 결재내용.objects.all()
#     serializer_class = serializers.결재내용_Serializer

# class 생산지시_의뢰_ViewSet(생산지시_ViewSet):
#     qs = 생산지시.objects.order_by('-id')
#     def get_queryset(self):       
#         return 생산지시.objects.filter(영업담당자 = self.request.user.user_성명, 의뢰여부=False).order_by('-id')
	
# class 생산지시_접수_ViewSet(생산지시_ViewSet):
#     qs = 생산지시.objects.order_by('-id')
#     def get_queryset(self):       
#         return 생산지시.objects.filter(접수여부=False, 의뢰여부=True).order_by('-id')
	
# class 생산지시_완료_ViewSet(생산지시_ViewSet):
#     qs = 생산지시.objects.order_by('-id')
#     def get_queryset(self):       
#         return 생산지시.objects.filter(완료여부=False, 접수여부=True).order_by('-id')
	

# class 생산지시_이력조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     qs = 생산지시.objects.order_by('-id')
#     serializer_class = serializers.생산지시_DB_Serializer 
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['구분', '고객사','현장명','상세내용','비고'] 
#     pagination_class = 생산지시_Pagination

#     def get_queryset(self):       
#         print ( 'search ??')
#         return 생산지시.objects.order_by('-id')
