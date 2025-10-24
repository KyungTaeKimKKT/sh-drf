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
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
# from rest_framework.authentication import TokenAuthentication, SessionAuthentication, BasicAuthentication
# from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
# from rest_framework_simplejwt.views import TokenObtainPairView
from datetime import datetime, date,time, timedelta

from util.customPermission import IS_Admin_Permission
from . import serializers
from util.customfilters import 생산계획실적_BG용_FilterSet

from 생산모니터링.models_외부 import (
    sensor, 
    sensor_기준정보, 
    order, 
    test_server, 
    NEW_SENSOR_생산_MASTER, 
    생산계획실적
)

from 생산모니터링.models import (
    무재해_DB, 
    생산계획_사용자_DB, 
    SENSOR_NETWORK_DB,  
    휴식시간_DB
)
# from 네트워크_monitor.ext_models import FPING_DB, FPING_생산모니터링_DB

class 무재해_DB_ViewSet(viewsets.ModelViewSet):
    MODEL = 무재해_DB
    queryset = MODEL.objects.filter(is_active=True).order_by('-id')  
    serializer_class = serializers.무재해_DB_Serializer
    
    def get_queryset(self):              
        return self.MODEL.objects.filter(is_active=True).order_by('-id')  


# sensor_기준정보.objects.using('New_생산모니터링')
class KIOSK_생산계획실적ViewSet(viewsets.ReadOnlyModelViewSet):
    """ 당일 생산계획실적 view set"""
    queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
    serializer_class = serializers.KIOSK_생산계획실적Serializer
    # disable authentication https://stackoverflow.com/questions/27085219/how-can-i-disable-authentication-in-django-rest-framework
    authentication_classes = []
    permission_classes = []
    # now = datetime.now()

    def get_queryset(self):              
        return 생산계획실적.objects.using('생산모니터링').filter(is_active=True, start_time__contains=date.today() ).order_by('sensor_id')  


class 당일생산계획ViewSet(viewsets.ModelViewSet):
    queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
    serializer_class = serializers.생산계획Serializer

    def get_queryset(self):
        qs = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today() ).order_by('sensor_id')  
        사용자instance = 생산계획_사용자_DB.objects.filter(사용자=self.request.user.user_성명)[0]
        return qs.filter(sensor_id__in = 사용자instance.사용List.split(',') )  
    
class 당일생산계획_bg용_ViewSet(viewsets.ModelViewSet):
    queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
    serializer_class = serializers.생산계획_BG용_Serializer
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # authentication_classes = []
    permission_classes = [IS_Admin_Permission]
    filterset_class = 생산계획실적_BG용_FilterSet

    # def get_queryset(self):
    #     # qs = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today()-timedelta(days=0) ).order_by('sensor_id')  
    #     qs = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
    #     return qs


# class manage_DB_gen생산capa(APIView):
#     authentication_classes = []
#     permission_classes = []
#     def post(self, request):
#         queryset = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today() ).order_by('sensor_id')
#         for instance in queryset:
#             instance.save()

#         return Response({'status': 200, 'action': False})

class sensor_기준정보ViewSet(viewsets.ModelViewSet):
    queryset = sensor_기준정보.objects.using('생산모니터링').filter(is_active=True).order_by('sensor_id')  
    serializer_class = serializers.sensor_기준정보Serializer

    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
    ]
    search_fields =['ip_주소'] 

    def get_queryset(self):
        return sensor_기준정보.objects.using('생산모니터링').filter(is_active=True).order_by('sensor_id') 


class 당일생산계획_for_sensor_ViewSet(viewsets.ModelViewSet):
    queryset = 생산계획실적.objects.using('생산모니터링').order_by('-id')
    serializer_class = serializers.KIOSK_생산계획실적Serializer

    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
    ]
    search_fields =['ip_address'] 

    def get_queryset(self):
        now = datetime.now()
        start = datetime(now.year, now.month, now.day, hour=0, minute=0, second=0)
        end = datetime(now.year, now.month, now.day, hour=23, minute=59, second=59)
        queryset = 생산계획실적.objects.using('생산모니터링').filter(start_time__gte = start, start_time__lte=end ).order_by('sensor_id')  
        return queryset