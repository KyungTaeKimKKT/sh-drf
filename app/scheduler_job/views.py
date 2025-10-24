"""
Views for the 품질경영 APIs
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
from django.db import transaction, models
from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.conf import settings
from datetime import datetime, date,time, timedelta
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
import redis
from django.core.cache import cache
from . import serializers as Scheduler_Job_Serializers
from . import models as Scheduler_Job_Models
# from . import customfilters
from util import utils_func as Utils


import logging, traceback
logger = logging.getLogger('config')

class JOB_INFO_ViewSet(viewsets.ModelViewSet):
    MODEL = Scheduler_Job_Models.JOB_INFO
    # div, name = 'Scheduler_Job', 'JOB_INFO'
    # TABLE_NAME = f"{div}_{name}_appID_{Utils.get_tableName_from_api권한(div=div, name=name)}"

    queryset = MODEL.objects.all()
    serializer_class = Scheduler_Job_Serializers.JOB_INFO_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['name', 'job_function', 'description'] 
    # filterset_class = customfilters.Table_Config_Filter
    ordering_fields = ['name', 'created_at']
    ordering = ['name', '-created_at']
 

    def get_queryset(self):
        return self.MODEL.objects.select_related("ws_url_db").order_by( *self.ordering )
    
    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request, *args, **kwargs):
        """ 템플릿 생성 """
        instance = self.MODEL()
        serializer = self.get_serializer(instance)
        data = serializer.data.copy()
        data['id'] = -1
        data['created_at'] = datetime.now().isoformat()
        return Response(status=status.HTTP_200_OK, data= data )
    
class Scheduler_Job_Names_ApiView(APIView):
    def get(self, request, *args, **kwargs):
        qs = Scheduler_Job_Models.JOB_INFO.objects.filter(is_active=True).values('id','name')
        return Response(status=status.HTTP_200_OK, data=list(qs))
    

class Scheduler_Job_ViewSet(viewsets.ModelViewSet):
    MODEL = Scheduler_Job_Models.Scheduler_Job
    queryset = MODEL.objects.all()
    serializer_class = Scheduler_Job_Serializers.Scheduler_Job_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['job_info__name', 'job_info__job_function', 'job_info__description'] 
    # filterset_class = customfilters.Table_Config_Filter
    ordering_fields = ['job_info__name', 'job_info__created_at']
    ordering = ['job_info__name', '-job_info__created_at']

    # Utils.generate_table_config_db_from_viewset(
    #     MODEL=MODEL,
    #     div='Scheduler_Job',
    #     name='Schedule',
    #     serializer=Scheduler_Job_Serializers.Scheduler_Job_Serializer()
    # )

    def get_queryset(self):
        return (self.MODEL.objects
                .prefetch_related('job_info')
                .order_by( *self.ordering )
        )
    
    def perform_create(self, serializer):        
        serializer.save(created_by=self.request.user, updated_by=self.request.user  )
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request, *args, **kwargs):
        """ 템플릿 생성 """
        instance = self.MODEL()
        serializer = self.get_serializer(instance)
        data = serializer.data.copy()
        data['id'] = -1
        data['created_time'] = datetime.now().isoformat()
        data['updated_time'] = datetime.now().isoformat()
        return Response(status=status.HTTP_200_OK, data= data )


class Scheduler_Job_Status_ViewSet(viewsets.ModelViewSet):
    MODEL = Scheduler_Job_Models.Scheduler_Job_Status
    queryset = MODEL.objects.all()
    serializer_class = Scheduler_Job_Serializers.Scheduler_Job_Status_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['job__job_info__name', 'job__job_info__job_function', 'job__job_info__description'] 
    ordering_fields = ['job__job_info__name', 'start_time', 'end_time']
    ordering = [ '-start_time', '-end_time']

    def get_queryset(self):
        return (self.MODEL.objects
                .prefetch_related('job', 'job__job_info')
                .order_by( *self.ordering )
        )



class Scheduler_Job_Log_ViewSet(viewsets.ModelViewSet):
    MODEL = Scheduler_Job_Models.Scheduler_Job_Log
    queryset = MODEL.objects.all()
    serializer_class = Scheduler_Job_Serializers.Scheduler_Job_Log_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['job__job_info__name', 'job__job_info__job_function', 'job__job_info__description'] 
    ordering_fields = ['job__job_info__name', 'created_time']
    ordering = ['-created_time']

    def get_queryset(self):
        return (self.MODEL.objects
                .prefetch_related('job', 'job__job_info')
                .order_by( *self.ordering )
        )
