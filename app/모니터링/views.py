"""
Views for the 모니터링 APIs
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
from django.db import transaction
from rest_framework.parsers import MultiPartParser,FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from datetime import datetime, date,timedelta

from django.http import QueryDict
import json, time
import pandas as pd
from django.utils.dateparse import parse_date

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )

from .serializers import  (
    Log_login_Serializer,
    Log_사용App_Serializer,
    사내IP_Serializer,
    사내IP_PING결과_Serializer,
    사내IP_PING결과_Image_Serializer,
)
# from . import customfilters

from .models import (
    Log_login, 
    Log_사용App,
    사내IP,
    사내IP_PING결과,
    사내IP_PING결과_Image,
)

from subprocess import PIPE, run
import psutil

from util.base_model_viewset import BaseModelViewSet
from . import models, serializers

class Server_Monitor (APIView):

    def get(self, request, format=None):
        """
        Return server status.
        """
        result = {
            'cpu_percentage' : psutil.cpu_percent(),
            'cpu_count' : psutil.cpu_count(),
            'memory'  : psutil.virtual_memory(),
            'disk_usage' : psutil.disk_usage('/'),
            'network_usage' : self._get_Net_usage(),
        }

        return Response(data=result, status=status.HTTP_200_OK )
    
    # https://stackoverflow.com/questions/62020140/psutil-network-monitoring-script
    def _get_Net_usage(self, inf = 'enp3s0'):
        #change the inf variable according to the interface

        net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
        net_in_1 = net_stat.bytes_recv
        net_out_1 = net_stat.bytes_sent
        time.sleep(1)
        net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
        net_in_2 = net_stat.bytes_recv
        net_out_2 = net_stat.bytes_sent

        net_in = round((net_in_2 - net_in_1) / 1024 / 1024, 3)
        net_out = round((net_out_2 - net_out_1) / 1024 / 1024, 3)
        # print(f"Current net-usage:\nIN: {net_in} MB/s, OUT: {net_out} MB/s")
        return { 'net_in' : net_in, 'net_out': net_out} # 단위 MB/s




class 동시접속자수 ( APIView):

    def post(self, request, format=None):

        if 시간간격:= request.data.get('시간간격'):
            if( 시간간격 == '분') :
                end = datetime.now()
                start = end - timedelta(hours=1)
                qs = Log_사용App.objects.filter( timestamp__range=[start, end])
                df = pd.DataFrame( list (qs.order_by('-id').values() ) )
                print (df)
                df['접속시간'] = pd.to_datetime( df['timestamp'].dt.strftime('%Y-%m-%d %H:%M') )
                # df['접속시간'] = pd.to_datetime( df['timestamp'], format='%Y-%m-%d %H:%M')
                print (df)
                df_pivot = df.pivot_table( index=['접속시간'], columns=['구분'], values=['user_fk_id'], aggfunc='count').fillna(0)
                # df_pivot = df.pivot_table( index=['구분', 'app'], columns=['접속시간'], values=['user_fk_id'], aggfunc='count').fillna(0)
                df_pivot.sort_index(axis=1, ascending=False)
                print (df_pivot)

                newColumn= []
                for cols in df_pivot.columns.values:
                    for col in cols:
                        if  col != 'user_fk_id':
                            newColumn.append(col)
                df_pivot.columns = newColumn

                df_sorted = df_pivot.sort_index(axis=0, ascending=False)
                df_ = df_sorted.reset_index()
                print ( df_)
                json = df_.to_json(orient='records', force_ascii=False, )
                chart_data = [df_.columns.tolist()] + df_.values.tolist()
                return Response(data=chart_data, status=status.HTTP_200_OK )

        if ping_test:= request.data.get('ping-test'):
            result = {}
            for _obj in 사내IP.objects.all():
                _instance, _created = 사내IP_PING결과.objects.get_or_create(사내IP_fk= _obj)                
                command = ["ping", "-c", "1", _obj.IP_주소]
                res = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                _instance.결과 =  not res.returncode
                _instance.save( )
                result[_obj.IP_주소] = not res.returncode

            return Response(data=result, status=status.HTTP_200_OK )


class Log_login_ViewSet(viewsets.ModelViewSet):
    """ log-in 관리자용 view set """    
    queryset = Log_login.objects.order_by('-id')
    serializer_class = Log_login_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return Log_login.objects.order_by('-id')
    
    # https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
    # def create(self, request, *args, **kwargs):
    #     print (' view create내 ', request.data)

    #     부적합상세 = request.FILES.getlist('부적합상세')  if request.FILES.getlist('부적합상세') else []
    #     품질비용 = json.loads( request.data.get('품질비용') )  if request.data.get('품질비용') else []

    #     serializer = self.get_serializer(data=request.data, 부적합상세 =부적합상세  ,품질비용= 품질비용,  partial=True )

    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     # return Response({'status': 200})
    #     return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # def update(self, request, *args, **kwargs):
    #     # main thing starts
    #     instance = self.get_object()
    #     부적합상세 = request.FILES.getlist('부적합상세')  if request.FILES.getlist('부적합상세') else []
    #     품질비용 = json.loads( request.data.get('품질비용') )  if request.data.get('품질비용') else []


    #     serializer = self.get_serializer(instance, data=request.data, 부적합상세 =부적합상세  ,
    #                                      품질비용= 품질비용,   partial=True )
    #     # main thing ends

    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     # return Response({'status': 200})
    #     return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
    

# class 모니터링_Modal_ViewSet(모니터링_ViewSet):
#     """ 모니터링 관리자용 view set """    

#     def get_queryset(self):       
#         today = date.today()
#         user_id = self.request.user.id
#         qs = 모니터링.objects.filter(is_Popup=True, popup_시작일__lte = today, popup_종료일__gte = today ).order_by('-id')
#         for _instance in qs:
#             if ( not 모니터링_Reading.objects.filter( 모니터링_fk = _instance.id, user=user_id, 
#                 timestamp__year=today.year, timestamp__month=today.month, timestamp__day=today.day).count() ):
#                 return qs
#         return []
    

# class 모니터링_Reading_ViewSet(viewsets.ModelViewSet):
    # """ 모니터링 reading 관리 view set """    
    # queryset = 모니터링_Reading.objects.order_by('-id')
    # serializer_class = 모니터링_Reading_Serializer
    # parser_classes = [MultiPartParser,FormParser]
    # filter_backends = [
    #        SearchFilter, 
    #        filters.DjangoFilterBackend,
    #     ]
    # # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # # pagination_class = 생산지시_Pagination

    # def get_queryset(self):       
    #     qs = 모니터링_Reading.objects.order_by('-id')
    #     return qs

class Log_사용App_ViewSet(viewsets.ModelViewSet):
    """ log-사용App 관리자용 view set """    
    queryset = Log_사용App.objects.order_by('-id')
    serializer_class = Log_사용App_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return Log_사용App.objects.order_by('-id')

class 사내IP_ViewSet(viewsets.ModelViewSet):
    """ 사내IP 관리자용 view set """    
    MODEL = 사내IP
    queryset = MODEL.objects.order_by('-id')
    serializer_class = 사내IP_Serializer
    # parser_classes = [MultiPartParser,FormParser, JSONParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    authentication_classes = []
    permission_classes = []
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return self.MODEL.objects.order_by('id')
    
    #  bulk create or update 
    @action(detail=False, methods=['post'], url_path='bulk_create_or_update')
    def bulk_create_or_update(self, request, *args, **kwargs):
        try:
            datas = request.data.get('datas')
            datas = json.loads(datas)
            bulk_create_list = []
            bulk_update_list = []
            for data in datas:
                
                if data['id'] >0 :
                    bulk_update_list.append(self.MODEL(**data))
                else:
                    data.pop('id')
                    bulk_create_list.append(self.MODEL(**data))

            with transaction.atomic():
                self.MODEL.objects.bulk_create(bulk_create_list)
                self.MODEL.objects.bulk_update(bulk_update_list, 
                    ['Category', 'host_이름', 'host_설명', 'MAC_주소', '비고', '상위IP', 'rel_x', 'rel_y'])
            return Response(data=datas, status=status.HTTP_200_OK )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST )
        
    @action(detail=False, methods=['post'], url_path='batch_create_or_update')
    def batch_create_or_update(self, request, *args, **kwargs):
        try:
            datas = request.data.get('datas')
            datas = json.loads(datas)
            
            sent_ids = []  # 클라이언트에서 보낸 id 목록
            with transaction.atomic():
                for data in datas:
                    try:
                        id = data.pop('id')
                    except KeyError:
                        id = None

                    if id and id > 0:
                        sent_ids.append(id)
                        instance = self.MODEL.objects.get(id=id)
                        serializer = self.get_serializer(instance=instance, data=data)
                    else:
                        serializer = self.get_serializer(data=data)

                    serializer.is_valid(raise_exception=True)
                    instance = serializer.save()

                    if instance.id:  # 새로 생성된 경우에도 ID 수집
                        sent_ids.append(instance.id)

                # 🔥 여기에 삭제 로직 추가
                self.MODEL.objects.exclude(id__in=sent_ids).delete()

                qs = self.MODEL.objects.all()
                serializer = self.get_serializer(qs, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        


    def get_serializer_class(self):
        if self.action == 'list':
            return 사내IP_Serializer
        return super().get_serializer_class()

class 사내IP_PING결과_ViewSet(viewsets.ModelViewSet):
    """ 사내IP 관리자용 view set """    
    queryset = 사내IP_PING결과.objects.order_by('-id')
    serializer_class = 사내IP_PING결과_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 생산지시_Pagination

    # def get_queryset(self):       
    #     return 사내IP_PING결과.objects.all()

class 사내IP_PING결과_IMAGE_ViewSet(viewsets.ModelViewSet):
    """ 사내IP 관리자용 view set """
    MODEL =   사내IP_PING결과_Image  
    queryset = MODEL.objects.order_by('-id')
    serializer_class = 사내IP_PING결과_Image_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    authentication_classes = []
    permission_classes = []
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 생산지시_Pagination

    # def get_queryset(self):       
    #     return 사내IP_PING결과.objects.all()

#### 25-7-7 
class ApiAccessLog_ViewSet(BaseModelViewSet):
    http_method_names = ['get']
    MODEL = models.ApiAccessLog
    queryset = MODEL.objects.all()
    serializer_class = serializers.ApiAccessLog_Serializer
    parser_classes = [ JSONParser, MultiPartParser, FormParser]
    search_fields = ['user__user_성명', 'method', 'path', 'query_params']
    ordering_fields = ['id']
    ordering = ['-id']

    def get_queryset(self):
        return self.MODEL.objects.all()
    
#### 25-8-7
class Client_App_Access_Log_ViewSet(BaseModelViewSet):
    http_method_names = ['get']
    MODEL = models.Client_App_Access_Log
    queryset = MODEL.objects.all()
    serializer_class = serializers.Client_App_Access_Log_Serializer
    parser_classes = [ JSONParser, MultiPartParser, FormParser]
    search_fields = ['user__user_성명', 'app_fk__app_이름', 'status']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        return self.MODEL.objects.all()
