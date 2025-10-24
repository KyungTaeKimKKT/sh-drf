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
from . import serializers_new
from util.customfilters import 생산계획실적_BG용_FilterSet

import 생산모니터링.models_외부 as Models_외부
import 생산모니터링.models as Models
from django.db import transaction
import time
# from 네트워크_monitor.ext_models import FPING_DB, FPING_생산모니터링_DB

class 무재해_DB_ViewSet(viewsets.ModelViewSet):
    MODEL = Models.무재해_DB
    queryset = MODEL.objects.filter(is_active=True).order_by('-id')  
    serializer_class = serializers_new.무재해_DB_Serializer
    
    def get_queryset(self):              
        return self.MODEL.objects.filter(is_active=True).order_by('-id')  
    
class Sensor_기준정보_ViewSet(viewsets.ModelViewSet):
    MODEL = Models_외부.sensor_기준정보
    queryset = MODEL.objects.filter(is_active=True).order_by('-id')  
    serializer_class = serializers_new.sensor_기준정보Serializer
    
    def get_queryset(self):              
        return self.MODEL.objects.order_by('-id') 

class 휴식시간_DB_ViewSet(viewsets.ModelViewSet):
    MODEL = Models.휴식시간_DB
    queryset = MODEL.objects.order_by('-id')  
    serializer_class = serializers_new.휴식시간_DB_Serializer
    
    def get_queryset(self):              
        return self.MODEL.objects.order_by('-id') 
    
class 생산계획실적_DB_ViewSet(viewsets.ModelViewSet):
    MODEL = Models_외부.생산계획실적
    now = datetime.now()
    queryset  =Models_외부.생산계획실적.objects.using('생산모니터링').filter( start_time__date = now.date()  ).order_by('sensor_id') 
    serializer_class = serializers_new.생산계획실적_DB_Serializer
    authentication_classes = []
    permission_classes = []
    
    def get_queryset(self):            
        now = datetime.now() 
        return Models_외부.생산계획실적.objects.using('생산모니터링').filter( start_time__date = now.date()  ).order_by('sensor_id') 
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print ( '1 :', self, queryset.count() )
        if queryset.count() == 0:
            self.create_if_empty()
            queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        print ( '2 :', self, serializer.data )
        return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        print ( '2 :', self, page )
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            print ( '3 :', self, serializer.data )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        print ( '4 :', self, serializer.data )
        return Response(serializer.data)
        # return super().list(request, *args, **kwargs)

    @transaction.atomic
    def create_if_empty(self):
        max_count = 10
        today = datetime.now().date()
        query_date = today - timedelta(days=1)
        while max_count > 0:
            qs = Models_외부.생산계획실적.objects.using('생산모니터링').filter( start_time__date = query_date  ).order_by('sensor_id') 
            if qs.count() == 0:
                max_count -= 1
                query_date -= timedelta(days=1)
            else:
                break
        if qs.count() > 0:
            for _inst in qs:
                n_start_time = datetime(today.year, today.month, today.day, hour=_inst.start_time.hour, minute=_inst.start_time.minute, second=_inst.start_time.second)
                n_end_time = datetime(today.year, today.month, today.day, hour=_inst.end_time.hour, minute=_inst.end_time.minute, second=_inst.end_time.second)
                Models_외부.생산계획실적.objects.using('생산모니터링').create(
                    sensor_id = _inst.sensor_id,
                    line_no = _inst.line_no,
                    start_time = n_start_time,
                    end_time = n_end_time,
                    plan_qty = _inst.plan_qty,
                    job_qty = 0,
                    oper_yn = _inst.oper_yn,
                    등록자 = 'admin',
                    is_active = _inst.is_active,
                    ip_address = _inst.ip_address,
                    job_qty_time= n_start_time 
                )

class 예상생산실적_View(APIView):
    """ 생산게획과 휴식시간으로 , 해당 생산 예상시간을 list로 response"""
    MODEL_생산계획 = Models_외부.생산계획실적
    MODEL_휴식 = Models.휴식시간_DB
    MODEL_SENSOR_기준정보 = Models_외부.sensor_기준정보
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        s = time.time()
        now = datetime.now()
        res = {}
        for _instance in  Models_외부.생산계획실적.objects.using('생산모니터링').filter( start_time__date = now.date()  ).order_by('sensor_id'):
            QS_휴식 =  Models.휴식시간_DB.objects.filter( 적용대상__contains = _instance.sensor_id )
            예상생산실적_list = self.__generate_예상생산실적(_instance, QS_휴식)
            res[ _instance.sensor_id ] =  예상생산실적_list

        # print ( self, self.__calcurate_예상생산수량(curTime=datetime.now(), 예상시간List=res['S-01']))
        print (self, '소요시간: ', time.time() -s )
        return Response (res )
    
    def __generate_예상생산실적(self, _instance:Models_외부.생산계획실적, QS_휴식:list[ Models.휴식시간_DB] ) -> list:
        tact_time : int = Models_외부.sensor_기준정보.objects.using('생산모니터링').get( sensor_id = _instance.sensor_id ).tact_time
        start_time: datetime = _instance.start_time
        end_time : datetime = _instance.end_time

        휴식시간_List = [( _instance.휴식시간_시작 , _instance.휴식시간_종료)  for _instance in QS_휴식 ]
        # print ( self, QS_휴식 , 휴식시간_List )
        예상생산_time_List = [start_time]
        예상생산_time = start_time
        while 예상생산_time < end_time:
            예상생산_time += timedelta(seconds=tact_time)
            if self.__is_휴식시간 ( 휴식시간_List, 예상생산_time.time() ):
                continue
            else:
                예상생산_time_List.append(예상생산_time)
        
        return 예상생산_time_List

    def __is_휴식시간( self, 휴식시간_List:list[tuple[datetime.time, datetime.time]] , 예상생산_time:datetime.time ) -> bool:
        for (start_time, end_time) in 휴식시간_List:
            if start_time <= 예상생산_time <= end_time:
                return True
        return False

    def __calcurate_예상생산수량( self, curTime:datetime , 예상시간List:list[datetime]) -> int:
        for idx, _time in enumerate(예상시간List):
            if idx < len(예상시간List) -1:
                if _time < curTime <= 예상시간List[idx+1]:
                    return idx+1



# # sensor_기준정보.objects.using('New_생산모니터링')
# class KIOSK_생산계획실적ViewSet(viewsets.ReadOnlyModelViewSet):
#     """ 당일 생산계획실적 view set"""
#     queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
#     serializer_class = serializers.KIOSK_생산계획실적Serializer
#     # disable authentication https://stackoverflow.com/questions/27085219/how-can-i-disable-authentication-in-django-rest-framework
#     authentication_classes = []
#     permission_classes = []
#     # now = datetime.now()

#     def get_queryset(self):              
#         return 생산계획실적.objects.using('생산모니터링').filter(is_active=True, start_time__contains=date.today() ).order_by('sensor_id')  


# class 당일생산계획ViewSet(viewsets.ModelViewSet):
#     queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
#     serializer_class = serializers.생산계획Serializer

#     def get_queryset(self):
#         qs = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today() ).order_by('sensor_id')  
#         사용자instance = 생산계획_사용자_DB.objects.filter(사용자=self.request.user.user_성명)[0]
#         return qs.filter(sensor_id__in = 사용자instance.사용List.split(',') )  
    
# class 당일생산계획_bg용_ViewSet(viewsets.ModelViewSet):
#     queryset = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
#     serializer_class = serializers.생산계획_BG용_Serializer
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     # authentication_classes = []
#     permission_classes = [IS_Admin_Permission]
#     filterset_class = 생산계획실적_BG용_FilterSet

#     # def get_queryset(self):
#     #     # qs = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today()-timedelta(days=0) ).order_by('sensor_id')  
#     #     qs = 생산계획실적.objects.using('생산모니터링').order_by('sensor_id')  
#     #     return qs


# # class manage_DB_gen생산capa(APIView):
# #     authentication_classes = []
# #     permission_classes = []
# #     def post(self, request):
# #         queryset = 생산계획실적.objects.using('생산모니터링').filter(start_time__contains=date.today() ).order_by('sensor_id')
# #         for instance in queryset:
# #             instance.save()

# #         return Response({'status': 200, 'action': False})

# class sensor_기준정보ViewSet(viewsets.ModelViewSet):
#     queryset = sensor_기준정보.objects.using('생산모니터링').filter(is_active=True).order_by('sensor_id')  
#     serializer_class = serializers.sensor_기준정보Serializer

#     filter_backends = [
#         SearchFilter, 
#         filters.DjangoFilterBackend,
#     ]
#     search_fields =['ip_주소'] 

#     def get_queryset(self):
#         return sensor_기준정보.objects.using('생산모니터링').filter(is_active=True).order_by('sensor_id') 


# class 당일생산계획_for_sensor_ViewSet(viewsets.ModelViewSet):
#     queryset = 생산계획실적.objects.using('생산모니터링').order_by('-id')
#     serializer_class = serializers.KIOSK_생산계획실적Serializer

#     filter_backends = [
#         SearchFilter, 
#         filters.DjangoFilterBackend,
#     ]
#     search_fields =['ip_address'] 

#     def get_queryset(self):
#         now = datetime.now()
#         start = datetime(now.year, now.month, now.day, hour=0, minute=0, second=0)
#         end = datetime(now.year, now.month, now.day, hour=23, minute=59, second=59)
#         queryset = 생산계획실적.objects.using('생산모니터링').filter(start_time__gte = start, start_time__lte=end ).order_by('sensor_id')  
#         return queryset