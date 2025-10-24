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
from . import serializers
from util.customfilters import 작업지침_DB_FilterSet
# from . import customfilters

from .models import (
    첨부file, 
    Process, 
    작업지침,
    Group작업지침,
    결재내용,
    의장도file,
    의장도,
)


class 작업지침_fields_List(APIView):

    def get(self, request, format=None):
        """
        Return a list of all 작업지침 fileds.
        """
        fields = [f.name for f in 작업지침._meta.fields] + ['process_fks' , '첨부file_fks', 'Group작업지침','inputFields']
        fields_obj = { f:'' for f in fields}
        
        fields_obj['id'] = 'new'
        return Response(fields_obj)

class 작업지침_ViewSet(viewsets.ModelViewSet):
    """ 작업지침 관리자용 view set """    
    queryset = 작업지침.objects.order_by('-id')
    serializer_class = serializers.작업지침_Serializer 
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['제목','proj_No'] 
    filterset_class =  작업지침_DB_FilterSet
    
    def get_queryset(self):       
        return 작업지침.objects.order_by('-id')
    
    # https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
    def create(self, request, *args, **kwargs):
        print ('create :\n', request.data)

        serializer = self.get_serializer(data=request.data, fks=self._get_kwarg_for_serializer(request) )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, fks=self._get_kwarg_for_serializer(request), partial=True )

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)

    
    def _get_kwarg_for_serializer(self, request) -> dict:
        print ( request.data , request.data.get('첨부file_fks_json'))
        return {
            'process_fks' : json.loads( request.data.get('process_fks') ) if request.data.get('process_fks') else [],
            # '결재내용_fks' : json.loads( request.data.get('결재내용_fks') ) if  request.data.get('결재내용_fks') else [],
            'el_info_fks' : json.loads( request.data.get('el_info_fks') ) if request.data.get('el_info_fks') else [],
            '첨부file_fks' : request.FILES.getlist('첨부file_fks') if  request.FILES.getlist('첨부file_fks') else [],
            # '의장도file_fks' :request.FILES.getlist('의장도file_fks') if  request.FILES.getlist('의장도file_fks') else [],
            '첨부file_fks_json' : json.loads( request.data.get('첨부file_fks_json' ) ) if  request.data.get('첨부file_fks_json') else [],
            'Rendering_file' : request.FILES.get('Rendering_file', None),
        }


class 작업지침_Dashboard_ViewSet(작업지침_ViewSet):
    pass


class 작업지침_결재_ViewSet (작업지침_ViewSet ):
    serializer_class = serializers.작업지침_결재_Serializer 
   
    def get_queryset(self):       
        qs = 작업지침.objects.order_by('-id')
        return qs.filter( 결재내용_fks__결재자 = self.request.user.id , 결재내용_fks__결재결과= None )
    
    def update(self, request, *args, **kwargs):
        # main thing starts
        instance = self.get_object()
        결재내용_fks = json.loads( request.data.get('결재내용_fks') ) if  request.data.get('결재내용_fks') else []

        serializer = self.get_serializer(instance, data=request.data, 결재내용_fks=결재내용_fks, partial=True )
        # main thing ends

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        # return Response({'status': 200})
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)



class 작업지침_등록_ViewSet(작업지침_ViewSet):

    def get_queryset(self):
        qs = 작업지침.objects.filter( 진행현황__icontains ='작성', 작성자 = self.request.user.user_성명, Rev = 1 ).order_by('-id')
        return qs
    
class 작업지침_ECO_ViewSet(작업지침_ViewSet):

    def get_queryset(self):
        qs = 작업지침.objects.filter( 진행현황='작성', 작성자 = self.request.user.user_성명, Rev__gte = 2 ).order_by('-id')
        return qs

 
class 작업지침_진행현황_ViewSet (작업지침_ViewSet ):
   
    def get_queryset(self):       
        qs = 작업지침.objects.order_by('-id')
        return qs.filter( 결재내용_fks__결재자 = self.request.user.id  )
    
    
class 작업지침_배포_ViewSet (작업지침_ViewSet ):
   
    # 진행현황은 model save  할때, method 로 status 계산해서 저장함
    def get_queryset(self):       
        qs = 작업지침.objects.order_by('-id')
        return qs.filter(진행현황 = '배포')
 

class 의장도file_Viewset(viewsets.ModelViewSet):
    queryset = 의장도file.objects.order_by('-id')
    serializer_class = serializers.의장도file_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]

    def get_queryset(self):       
        return 의장도file.objects.order_by('-id')
    
class 의장도_Viewset(viewsets.ModelViewSet):
    queryset = 의장도.objects.order_by('-id')
    serializer_class = serializers.의장도_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]

    def get_queryset(self):       
        return 의장도.objects.order_by('-id')
    

class 결재내용_ViewSet(viewsets.ModelViewSet):
    queryset = 결재내용.objects.all()
    serializer_class = serializers.결재내용_Serializer

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
