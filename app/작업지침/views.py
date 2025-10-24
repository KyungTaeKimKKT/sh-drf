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
from .customPage import CustomPagination
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

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )

from util.customfilters import 작업지침_DB_FilterSet

from . import models, serializers, customfilters


# ic.disable()

class 작업지침_Rendering_file_ViewSet(viewsets.ModelViewSet):
    """ 작업지침 Process view set """    
    MODEL = models.Rendering_file
    queryset = MODEL.objects.order_by('-id')
    serializer_class = serializers.Rendering_file_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    # filterset_class =  customfilters.작업지침_Process_FilterSet
    
    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id')


class 작업지침_첨부file_ViewSet(viewsets.ModelViewSet):
    """ 작업지침 Process view set """    
    MODEL = models.첨부file
    queryset = MODEL.objects.order_by('-id')
    serializer_class = serializers.첨부file_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    # filterset_class =  customfilters.작업지침_Process_FilterSet
    
    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id')

class 작업지침_Process_ViewSet(viewsets.ModelViewSet):
    """ 작업지침 Process view set """    
    MODEL = models.Process
    queryset = MODEL.objects.order_by('-id')
    serializer_class = serializers.Process_Serializer 
    # parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    filterset_class =  customfilters.작업지침_Process_FilterSet
    
    def get_queryset(self):       
        return self.MODEL.objects.order_by('표시순서','id')


class 작업지침_ViewSet(viewsets.ModelViewSet):
    """ 작업지침 관리자용 view set """    
    MODEL = models.작업지침
    queryset = MODEL.objects.order_by('-id')
    serializer_class = serializers.작업지침_Serializer 
    # parser_classes = [MultiPartParser,FormParser]
    # parser_classes = [ JSONParser ]

    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['제목','Proj_No'] 
    filterset_class =  customfilters.작업지침_DB_FilterSet
    
    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id')
    
    # def update(self, request, *args, **kwargs):
    #     ic (request.data)
    #     instance: models.작업지침 = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
        
    #     # 의장도_fks 필드가 빈 리스트로 전송된 경우 clear 처리
    #     if '의장도_fks' in request.data and request.data['의장도_fks'] == []:
    #         instance.의장도_fks.clear()
        
    #     self.perform_update(serializer)
    #     return Response(serializer.data)


class 작업지침_Dashboard_ViewSet(작업지침_ViewSet):
    pass


# class 작업지침_결재_ViewSet (작업지침_ViewSet ):
#     serializer_class = serializers.작업지침_결재_Serializer 
   
#     def get_queryset(self):       
#         qs = 작업지침.objects.order_by('-id')
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



class 작업지침_등록_ViewSet(작업지침_ViewSet):

    def get_queryset(self):
        qs = self.MODEL.objects.filter( is_배포=False, 작성자_fk = self.request.user, Rev = 1 ).order_by('-id')
        return qs
    
class 작업지침_ECO_ViewSet(작업지침_ViewSet):

    def get_queryset(self):
        qs = self.MODEL.objects.filter( is_배포=False, 작성자_fk = self.request.user, Rev__gte = 2 ).order_by('-id')
        return qs

 
class 작업지침_의장도_Update_ViewSet (작업지침_ViewSet ):
   
    def get_queryset(self):       
        qs = self.MODEL.objects.exclude(의장도_fks__isnull=False).filter( is_배포=True, 작성자_fk = self.request.user ).order_by('-id')
        return qs
    
    
class 작업지침_이력조회_ViewSet (작업지침_ViewSet ):
   
    # 진행현황은 model save  할때, method 로 status 계산해서 저장함
    def get_queryset(self):       
        qs = self.MODEL.objects.order_by('-id')
        return qs.filter(is_배포 = True)
 
    
class 의장도_Viewset(viewsets.ModelViewSet):
    MODEL = models.의장도
    queryset = MODEL.objects.order_by('-id')
    serializer_class = serializers.의장도_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    filterset_class =  customfilters.작업지침_의장도_FilterSet

    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id')
    

# class 결재내용_ViewSet(viewsets.ModelViewSet):
#     queryset = 결재내용.objects.all()
#     serializer_class = serializers.결재내용_Serializer

# class 작업지침_의뢰_ViewSet(작업지침_ViewSet):
#     qs = 작업지침.objects.order_by('-id')
#     def get_queryset(self):       
#         return 작업지침.objects.filter(영업담당자 = self.request.user.user_성명, 의뢰여부=False).order_by('-id')
    
# class 작업지침_접수_ViewSet(작업지침_ViewSet):
#     qs = 작업지침.objects.order_by('-id')
#     def get_queryset(self):       
#         return 작업지침.objects.filter(접수여부=False, 의뢰여부=True).order_by('-id')
    
# class 작업지침_완료_ViewSet(작업지침_ViewSet):
#     qs = 작업지침.objects.order_by('-id')
#     def get_queryset(self):       
#         return 작업지침.objects.filter(완료여부=False, 접수여부=True).order_by('-id')
    

# class 작업지침_이력조회_ViewSet(viewsets.ReadOnlyModelViewSet):
#     qs = 작업지침.objects.order_by('-id')
#     serializer_class = serializers.작업지침_DB_Serializer 
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     search_fields =['구분', '고객사','현장명','상세내용','비고'] 
#     pagination_class = 작업지침_Pagination

#     def get_queryset(self):       
#         print ( 'search ??')
#         return 작업지침.objects.order_by('-id')
