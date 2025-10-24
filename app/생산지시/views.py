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

from rest_framework.parsers import MultiPartParser,FormParser, JSONParser
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

from . import serializers, models, customfilters
from util.customfilters import 생산지시_DB_FilterSet



class 도면정보_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  models.도면정보
	queryset =  MODEL.objects.order_by('-id')   
	serializer_class = serializers.도면정보_Serializer  
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =[] 
	filterset_class =  customfilters.생산지시_도면정보_FilterSet

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('표시순서')
   
 
class HTM_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  models.Process
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.Process_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =[] 
	filterset_class =  customfilters.생산지시_Process_FilterSet

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('표시순서')
	

class SPG_Table_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL =  models.SPG_Table
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_Table_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =[] 
	filterset_class =  customfilters.생산지시_SPG_Table_FilterSet

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('표시순서')


class SPG_File_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = models.SPG_file
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')
	
class  TAB_Made_file_Viewset(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = models.TAB_Made_file
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers. TAB_Made_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')

# class 생산지시_fields_List(APIView):

# 	def get(self, request, format=None):
# 		"""
# 		Return a list of all 생산지시 fileds.
# 		"""
# 		fields = [f.name for f in 생산지시._meta.fields] + ['process_fks']
# 		fields_obj = { f:'' for f in fields}
		
# 		fields_obj['id'] = 'new'
# 		return Response(fields_obj)
	
class SPG_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	""" SPG 관리장용 view set """
	MODEL = models.SPG
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SPG_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# filterset_class =  customfilters.작업지침_Process_FilterSet
	search_fields =[''] 
	filterset_class =  customfilters.생산지시_SPG_FilterSet
	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')
	

class 생산지시_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	""" 생산지시 관리자용 view set """    
	MOEL = models.생산지시
	queryset = MOEL.objects.order_by('-id')
	serializer_class = serializers.생산지시_Serializer 
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# filterset_class =  customfilters.작업지침_Process_FilterSet
	search_fields =[] 
	filterset_class =  생산지시_DB_FilterSet
	

	def get_queryset(self):       
		return self.MOEL.objects.order_by('-id')
	

class JAMB_file_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = models.JAMB_file
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.JAMB_file_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')
	
class JAMB_발주정보_ViewSet(viewsets.ModelViewSet, Util_Model_Viewset):
	MODEL = models.JAMB_발주정보
	queryset =  MODEL.objects.order_by('-id')
	serializer_class = serializers.JAMB_발주정보_Serializer
	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = SPG_Pagination    

	def get_queryset(self):       
		return  self.MODEL.objects.order_by('-id')
	


# class 생산지시_JAMB_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
# 	""" 생산지시 JAMB 관리자용 view set """    
# 	MODEL = 생산지시
# 	queryset = 생산지시.objects.order_by('-id')
# 	serializer_class = serializers.생산지시_Serializer 
# 	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
# 	filterset_class =  생산지시_DB_FilterSet
	

# 	def get_queryset(self):       
# 		return self.MODEL.objects.order_by('-id')


# class 생산지시_배포_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
# 	""" 생산지시 배포 """
# 	MODEL = 생산지시
# 	queryset = 생산지시.objects.order_by('-id')
# 	serializer_class = serializers.생산지시_Serializer 
# 	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
# 	filterset_class =  생산지시_DB_FilterSet
	

# 	def get_queryset(self):       
# 		return self.MODEL.objects.filter(진행현황_htm='배포', 진행현황_jamb='배포').order_by('-id')

# class 생산지시_배포_생산계획대기_ViewSet(생산지시_ViewSet, Util_Model_Viewset):
# 	""" 생산지시 배포 """
# 	MODEL = 생산지시
# 	queryset = 생산지시.objects.order_by('-id')
# 	serializer_class = serializers.생산지시_Serializer 
# 	search_fields =['구분', '고객사','현장명','상세내용','비고'] 
# 	filterset_class =  생산지시_DB_FilterSet

# 	def get_queryset(self):       
# 		htm검색조건 = Q(진행현황_htm='배포') & ~Q(is_계획반영_htm =True) 
# 		jamb검색조건 = Q(진행현황_jamb='배포') & ~Q(is_계획반영_jamb =True) 
# 		queryset = self.MODEL.objects.filter( htm검색조건 | jamb검색조건).order_by('-id')		

# 		return queryset


