"""
Views for monitoring schedule
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

from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
# from datetime import datetime, date,time, timedelta
import datetime
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
from django.db.models import Q

from . import serializers

from .models import (
	Hour_Schedule,
	App,
)
from util.utils_viewset import Util_Model_Viewset
# from util.customfilters import NEWS_DB_FilterSet

class Hour_Schedule_ViewSet(viewsets.ModelViewSet):
	MODEL = Hour_Schedule
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.Hour_Schedule_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class App_ViewSet(viewsets.ModelViewSet):
	MODEL = App
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.App_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')	


# class NEWS_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = NEWS_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.NEWS_DB_Serializer
# 	filter_backends = [
# 		#    SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	filterset_class = NEWS_DB_FilterSet

# 	authentication_classes = []
# 	permission_classes = []

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	

# class NEWS_Table_Head_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = NEWS_Table_Head_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.NEWS_Table_Head_DB_Serializer
# 	filter_backends = [
# 		#    SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	# filterset_class =  Serial_DB_FilterSet

# 	authentication_classes = []
# 	permission_classes = []

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
	
	
# class NEWS_LOG_DB_ViewSet(viewsets.ModelViewSet ):
# 	MODEL = NEWS_LOG_DB
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = serializers.NEWS_LOG_DB_Serializer
# 	filter_backends = [
# 		#    SearchFilter, 
# 		   filters.DjangoFilterBackend,
# 		]
# 	# filterset_class =  Serial_DB_FilterSet

# 	authentication_classes = []
# 	permission_classes = []

# 	def get_queryset(self):
# 		return  self.MODEL.objects.order_by('-id')
