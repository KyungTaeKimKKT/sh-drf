"""
Views for 샘플관리 APIs
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

from .serializers import 샘플의뢰_Serializer #, 샘플결과_Serializer
# from . import customfilters

from .models import (
    첨부file, 
    Process, 
    샘플의뢰,
    # 샘플결과,
    Group작업지침,
    # 결재내용,
)


class 샘플관리_ViewSet(viewsets.ModelViewSet):
    """ 샘플의뢰 관리자용 view set """    
    queryset = 샘플의뢰.objects.order_by('-id')
    serializer_class = 샘플의뢰_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[ '고객사','요청건명','용도_현장명','현장명'] 
    # pagination_class = 샘플의뢰_Pagination

    def get_queryset(self):       
        return 샘플의뢰.objects.order_by('-id')
    
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
                                         fks=self._get_kwarg_for_serializer(request) )

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
    
    def _get_kwarg_for_serializer(self, request) -> dict:
        data = request.data
        files = request.FILES
        result = {
            # '품질비용_fk' : json.loads( 품질비용_fk ) if (품질비용_fk:=data.get('품질비용_fk')) else {},
            'process_fks' : json.loads( process_fks ) if (process_fks:= data.get('process_fks') ) else [],
            '첨부file_fks_삭제' :  첨부file_fks_삭제 if (첨부file_fks_삭제 := data.get('첨부file_fks_삭제')) else False,
            '첨부file_fks' : 첨부file_fks if  (첨부file_fks:=files.getlist('첨부file_fks')) else [],
            '첨부file_fks_json' : json.loads( 첨부file_fks_json ) if  (첨부file_fks_json:=data.get('첨부file_fks_json',[] ) ) else [],

            '완료file_fks' : 완료file_fks if  (완료file_fks:=files.getlist('완료file_fks')) else [],
           }

        return result

    # def destroy(self, request, *args, **kwargs):
    #     _instance = self.get_object()

    #     for obj in _instance.process_fks.all():
    #         obj.delete()

    #     _instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class 샘플의뢰_ViewSet(샘플관리_ViewSet):
    """ 샘플의뢰 사용자용 view set """    

    def get_queryset(self):       
        return 샘플의뢰.objects.filter( 요청자 = self.request.user.user_성명,
                                        진행현황__icontains = '작성' ).order_by('-id')
    
class 샘플완료_ViewSet(샘플관리_ViewSet):
    """ 샘플완료 사용자용 view set """    

    def get_queryset(self):       
        return 샘플의뢰.objects.filter( 진행현황__icontains = '배포' ).order_by('-id')

class 샘플이력조회_ViewSet(샘플관리_ViewSet):
    """ 샘플이력조회 사용자용 view set """    

    def get_queryset(self):       
        return 샘플의뢰.objects.exclude( 진행현황__icontains = '작성' ).order_by('-id')


# class 샘플완료_ViewSet(viewsets.ModelViewSet):
#     """ 샘플결과 관리자용 view set """    
#     queryset = 샘플결과.objects.order_by('-id')
#     serializer_class = 샘플결과_Serializer
#     parser_classes = [MultiPartParser,FormParser]
#     filter_backends = [
#            SearchFilter, 
#            filters.DjangoFilterBackend,
#         ]
#     # search_fields =['구분', '고객사','현장명','상세내용','비고'] 
#     # pagination_class = 샘플결과_Pagination

#     def get_queryset(self):       
#         print ('샘플결과_getList', 샘플결과.objects.order_by('-id'))
#         return 샘플결과.objects.order_by('-id')
    
#     # https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
#     def create(self, request, *args, **kwargs):
#         # print (request.data)

#         완료file_fks = request.FILES.getlist('완료file_fks')  if request.FILES.getlist('완료file_fks') else []

#         serializer = self.get_serializer(data=request.data, 완료file_fks=완료file_fks, 
#                                          partial=True )

#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

#     def update(self, request, *args, **kwargs):
#         # main thing starts
#         instance = self.get_object()
 
#         완료file_fks = request.FILES.getlist('완료file_fks') if  request.FILES.getlist('완료file_fks') else []

#         serializer = self.get_serializer(instance, data=request.data, 완료file_fks=완료file_fks,
#                                          partial=True )
#         # main thing ends

#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers)
    
#     # def destroy(self, request, *args, **kwargs):
#     #     _instance = self.get_object()

#     #     for obj in _instance.process_fks.all():
#     #         obj.delete()

#     #     _instance.delete()
#     #     return Response(status=status.HTTP_204_NO_CONTENT)




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


# class 작업지침_진행현황_ViewSet (작업지침_ViewSet ):
   
#     def get_queryset(self):       
#         qs = 작업지침.objects.order_by('-id')
#         return qs.filter( 결재내용_fks__결재자 = self.request.user.id  )
    
    
# class 작업지침_배포_ViewSet (작업지침_ViewSet ):
   
#     # 진행현황은 model save  할때, method 로 status 계산해서 저장함
#     def get_queryset(self):       
#         qs = 작업지침.objects.order_by('-id')
#         return qs.filter(진행현황 = '완료')
 


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
