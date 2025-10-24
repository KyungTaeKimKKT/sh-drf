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

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )
# from . import serializers

import 생산지시.serializers as 생지_serial
# from . import customfilters

from 생산지시.models import 생산지시
from 생산관리.models import 생산계획


# from .models import (
    # 하이생산계획,
#     도면상세내용, 
#     도면정보,
#     Process,
#     생산지시,
#     Group생산지시,
#     # 결재내용,
# )

# class 생산계획_생성(APIView):

#     def post(self, request, format=None):
#         """
#         Return a list of all 생산지시 fileds.
#         """

#         for 생산지시 in 생산지시.objects.order_by('-id') :
#             for process in 생산지시.process_fks.all():
#                 하이생산계획.objects.create( 생산지시_fk=생산지시, 생산지시_process_fk = process,
#                                       )
            

class 하이생산계획_ViewSet(viewsets.ModelViewSet):
    """ 하이생산 관리자용 view set """    
    queryset = 생산계획.objects.order_by('-id')
    serializer_class = 생지_serial.생산지시_Serializer 
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
    # pagination_class = 하이생산_Pagination

    def get_queryset(self):       
        return 생산지시.objects.order_by('-id')
    
    # https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)

        process_fks = json.loads( request.data.get('process_fks') )  if request.data.get('process_fks') else []
        도면정보_fks = json.loads( request.data.get('도면정보_fks') ) if request.data.get('도면정보_fks') else []

        serializer = self.get_serializer(data=request.data, 도면정보_fks=도면정보_fks ,process_fks= process_fks,  partial=True )
        # , 의장도file_fks=의장도file_fks,
        #                                  process_fks=process_fks,el_info_fks=el_info_fks )
        # serializer = self.get_serializer(data=request.data)
        # main thing ends

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # return Response({'status': 200})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # main thing starts
        instance = self.get_object()
        process_fks = json.loads( request.data.get('process_fks') )  if request.data.get('process_fks') else []
        도면정보_fks = json.loads( request.data.get('도면정보_fks') ) if request.data.get('도면정보_fks') else []


        serializer = self.get_serializer(instance, data=request.data, 도면정보_fks=도면정보_fks ,
                                         process_fks= process_fks,  partial=True )
        # main thing ends

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        # return Response({'status': 200})
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
    
    # def destroy(self, request, *args, **kwargs):
    #     _instance = self.get_object()

    #     for obj in _instance.process_fks.all():
    #         obj.delete()

    #     _instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)



# class 하이생산_결재_ViewSet (생산지시_ViewSet ):
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
