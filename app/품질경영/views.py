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

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )

from .serializers import NCR_Serializer, CS_Manage_Serializer, Action_Serializer, CS_Claim_Serializer, CS_Activity_Serializer, CS_Claim_File_Serializer, CS_Activity_File_Serializer, CS_Claim_Activity_Serializer
from . import customfilters

from .models import (
    NCR,
    부적합내용, 
    품질비용,
    CS_Manage,
    Action,
    Claim_File,
    ### fk 로 modeling
    CS_Claim,
    CS_Activity,
    CS_Claim_File,
    CS_Activity_File,
)


class NCR_ViewSet(viewsets.ModelViewSet):
    """ NCR 관리자용 view set """    
    queryset = NCR.objects.order_by('-id')
    serializer_class = NCR_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['발행번호', '제목','분류','조치사항','현장명','의장명','부적합상세','임시조치방안'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return NCR.objects.order_by('-id')
    
    # https://stackoverflow.com/questions/55315158/multiple-file-upload-drf
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)

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
            '품질비용_fk' : json.loads( 품질비용_fk ) if (품질비용_fk:=data.get('품질비용_fk')) else {},
            '부적합내용_fks' : json.loads( 부적합내용_fks ) if (부적합내용_fks:= data.get('부적합내용_fks') ) else [],
            'file_fks_삭제' :  file_fks_삭제 if (file_fks_삭제 := data.get('file_fks_삭제')) else False,
            'file_fks' : file_fks if  (file_fks:=files.getlist('file_fks')) else [],
            'file_fks_json' : json.loads( request.data.get('file_fks_json' ) ) if  request.data.get('file_fks_json') else [],
            # '의장도file_fks' :의장도file if  (의장도file:=files.getlist('의장도file') )else [],
           }

        return result

class NCR_등록_ViewSet(NCR_ViewSet):

    def get_queryset(self):       
        return NCR.objects.filter(is_배포=False, 
                                  작성자_fk = self.request.user
                                  ).order_by('-id')
    

class NCR_배포_ViewSet(NCR_ViewSet):

    def get_queryset(self):       
        return NCR.objects.filter(is_배포=True,
                                  
                                  ).order_by('-id')
    


class CS_Manage_ViewSet(viewsets.ModelViewSet):
    """ CS_Manage 관리자용 view set """    
    MODEL = CS_Manage
    queryset = CS_Manage.objects.order_by('-id').prefetch_related('action_fks', 'claim_file_fks').select_related('등록자_fk','el_info_fk')

    serializer_class = CS_Manage_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['현장명','불만요청사항','고객명'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id').prefetch_related('action_fks', 'claim_file_fks').select_related('등록자_fk','el_info_fk','완료자_fk')
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)

        # Claim_File에 해당하는 파일들을 저장
        claim_files = []
        for key, file in request.FILES.items():
            if key.startswith('file_'):
                # Claim_File 모델에 저장하는 로직
                claim_file_instance = Claim_File.objects.create(file=file)
                claim_files.append(claim_file_instance)

        # CS_Manage 인스턴스 생성
        mutable_data = request.data.copy()
        # claim_file_fks 필드가 ManyToManyField일 경우, 인스턴스의 ID 리스트로 변환 필요
        claim_files_fks = [cf.id for cf in claim_files]
        # mutable_data['claim_file_fks'] = claim_files_fks
        print ( 'claim_files_fks : ', claim_files_fks )
        serializer = self.get_serializer(data=mutable_data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print('Validation error:', serializer.errors)
            raise e
        cs_manage_instance = serializer.save()

        # Claim_File 인스턴스와 CS_Manage 인스턴스를 연결
        cs_manage_instance.claim_file_fks.set(claim_files_fks)

        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class Action_ViewSet(viewsets.ModelViewSet):
    """ Action 관리자용 view set """    
    MODEL = Action
    queryset = MODEL.objects.order_by('-id').prefetch_related('action_files')
    serializer_class = Action_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['현장명','불만요청사항','고객명'] 
    # pagination_class = 생산지시_Pagination

    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id').prefetch_related('action_files')
    


class CS_등록_ViewSet( CS_Manage_ViewSet ):
    def get_queryset(self):       
        return self.MODEL.objects.filter( 등록자_fk = self.request.user,
                                        진행현황__icontains = '작성' ).order_by('-id').prefetch_related('action_fks', 'claim_file_fks').select_related('등록자_fk','el_info_fk','완료자_fk')
    
class CS_활동_ViewSet( CS_Manage_ViewSet ):
    def get_queryset(self):       
        return self.MODEL.objects.filter( 진행현황__icontains = 'Open' ).order_by('-id').prefetch_related('action_fks', 'claim_file_fks').select_related('등록자_fk','el_info_fk','완료자_fk')
    
class CS_이력조회_ViewSet( CS_Manage_ViewSet ):
    def get_queryset(self):       
        return self.MODEL.objects.exclude( 진행현황__icontains = '작성' ).order_by('-id').prefetch_related('action_fks', 'claim_file_fks').select_related('등록자_fk','el_info_fk','완료자_fk')
    

### fk 로 modeling

class CS_Claim_ViewSet(viewsets.ModelViewSet):
    MODEL = CS_Claim
    queryset = MODEL.objects.all()
    serializer_class = CS_Claim_Serializer

    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
        #    SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['부적합유형'] 
    # search_fields =['현장명','불만요청사항','고객명'] 
    # search_fields =['현장명','불만요청사항','고객명','부적합유형'] 
    filterset_class =  customfilters.CS_Claim_FilterSet
    
    def get_queryset(self):
        queryset = self.MODEL.objects.order_by('-id').select_related(
                '등록자_fk','el_info_fk','완료자_fk'
            ).prefetch_related(
                'cs_activity_set__cs_activity_file_set',    # CS_Activity와 CS_Activity_File까지 최적화
                'cs_claim_file_set'                         # CS_Claim_File과의 관계 최적화
        )
        
        # 검색 필터 적용
        search = self.request.query_params.get('search', None)
        # print ( 'search : ', search )
        if search:
            queryset = queryset.filter(
                models.Q(현장명__icontains=search) |
                models.Q(불만요청사항__icontains=search) |
                models.Q(고객명__icontains=search) 
                # models.Q(부적합유형__icontains=search)
            )
        #     print ( 'queryset : ', queryset )
        #     print ( 'queryset.query : ', queryset.query )
        return queryset
    
    @action(detail=False, methods=['get'], url_path='등록')
    def get_등록(self, request):
        queryset = self.get_queryset().filter(등록자_fk = self.request.user,
                                            진행현황__icontains = '작성' )
        return queryset
    
    @action(detail=False, methods=['get'], url_path='get_Elevator사')
    def get_Elevator사(self, request):
        # 기본값 설정
        default_companies = ['현대', 'OTIS', 'TKE']
        
        # queryset에서 Elevator사 필드의 고유한 값 가져오기
        elevator_companies = self.MODEL.objects.values_list('Elevator사', flat=True).distinct()
        
        # 기본값을 먼저 추가하고, 기본값에 없는 엘리베이터 회사들을 추가
        combined_companies = default_companies + [company for company in elevator_companies if company and company not in default_companies]

        return Response(combined_companies)
    
    @action(detail=False, methods=['get'], url_path='get_부적합유형')
    def get_부적합유형(self, request):
        # 기본값 설정
        default_types = ['스크래치','이색',]
        
        # queryset에서 불량유형 필드의 고유한 값 가져오기
        types = self.MODEL.objects.values_list('부적합유형', flat=True).distinct()
        
        # 기본값을 먼저 추가하고, 기본값에 없는 불량유형들을 추가
        combined_types = default_types + [type for type in types if type and type not in default_types]
        print ( 'combined_types : ', combined_types )
        return Response(combined_types)


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)
        # Claim_File에 해당하는 파일들을 저장
        claim_files = request.FILES.getlist('claim_files')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        for file in claim_files:
            CS_Claim_File.objects.create(claim_fk=instance, file=file)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        print ( 'update내 ', request.data )
        instance = self.get_object()
        claim_files = request.FILES.getlist('claim_files')
                # 'claim_files_ids'가 요청 데이터에 있는 경우에만 처리
        if 'claim_files_ids' in request.data:
            existing_file_ids = request.data.getlist('claim_files_ids', [])
            # 모든 파일 삭제 조건
            if existing_file_ids == ['-1']:
                CS_Claim_File.objects.filter(claim_fk=instance).delete()
            else:
                # 기존 파일 삭제
                CS_Claim_File.objects.filter(claim_fk=instance).exclude(id__in=existing_file_ids).delete()
            
            # 기존 파일 삭제
            CS_Claim_File.objects.filter(claim_fk=instance).exclude(id__in=existing_file_ids).delete()
            print ( 'existing_file_ids : ', existing_file_ids )

        # 새로운 파일 추가
        for file in claim_files:
            CS_Claim_File.objects.create(claim_fk=instance, file=file)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 업데이트된 인스턴스를 다시 조회하여 직렬화
        updated_instance = self.MODEL.objects.get(id=instance.id)   
        updated_serializer = self.get_serializer(updated_instance)
        response_data = updated_serializer.data
                # 업데이트된 파일 목록을 응답 데이터에 포함
        # updated_file_ids = list(instance.cs_claim_file_set.values_list('id', flat=True))
        # response_data = serializer.data
        # response_data['updated_file_ids'] = updated_file_ids

        return Response(response_data)


class CS_Claim_등록_ViewSet(CS_Claim_ViewSet):

    def get_queryset(self):       
        # CS_Claim_ViewSet의 get_queryset을 호출하여 기본 쿼리셋을 가져옵니다.
        queryset = super().get_queryset()        
        # 추가적인 필터링을 적용합니다.
        return queryset.filter(등록자_fk=self.request.user, 
                               진행현황__icontains='작성')
    

class CS_Claim_활동_ViewSet(CS_Claim_ViewSet):

    def get_queryset(self):       
        # CS_Claim_ViewSet의 get_queryset을 호출하여 기본 쿼리셋을 가져옵니다.
        queryset = super().get_queryset()        
        # 추가적인 필터링을 적용합니다.
        return queryset.filter( 진행현황__icontains='Open')
    

class CS_Claim_이력조회_ViewSet(CS_Claim_ViewSet):

    def get_queryset(self):       
        # CS_Claim_ViewSet의 get_queryset을 호출하여 기본 쿼리셋을 가져옵니다.
        queryset = super().get_queryset()
        # 추가적인 필터링을 적용합니다.
        return queryset.filter( 진행현황__in=['Open','Close'])

 
class CS_Claim_Activity_ViewSet(viewsets.ModelViewSet):
    """ CS_Claim과 관련된 CS_Activity를 포함하는 view set """
    MODEL = CS_Claim
    queryset = MODEL.objects.all()
    serializer_class = CS_Claim_Serializer
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
        #    SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    # search_fields =['현장명','불만요청사항','고객명'] 
    filterset_class =  customfilters.CS_Claim_FilterSet

    def get_queryset(self):

        queryset =  self.MODEL.objects.order_by('-id').select_related(
                '등록자_fk',
                '완료자_fk',
                'el_info_fk'
            ).prefetch_related(
                'cs_activity_set__cs_activity_file_set',    # CS_Activity와 CS_Activity_File까지 최적화
                'cs_claim_file_set'                         # CS_Claim_File과의 관계 최적화
            )
        
        search = self.request.query_params.get('search', None)
        # print ( 'search : ', search )
        if search:
            queryset = queryset.filter(
                models.Q(현장명__icontains=search) |
                models.Q(불만요청사항__icontains=search) |
                models.Q(고객명__icontains=search) 
                # models.Q(부적합유형__icontains=search)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        # queryset = self.get_queryset()
        queryset = self.filter_queryset(self.get_queryset())  # 필터 적용
        response_data =[]
        for claim in queryset:
            claim_data = CS_Claim_Serializer(claim).data
            if claim.cs_activity_set.all():
                for activity in claim.cs_activity_set.all():
                    # 각 활동 정보를 추가
                    activity_data = CS_Activity_Serializer(activity).data
                # 클레임 정보와 활동 정보를 합쳐서 한 줄로 추가
                    activity_id = activity_data.pop('id')  # id 속성을 제거하고 저장
                    activity_data['activity_id'] = activity_id  # activity_id로 추가
                    combined_data = {**claim_data, **activity_data}
                    response_data.append(combined_data)
            else:
                response_data.append(claim_data)

        # 페이지네이션 적용
        page = self.paginate_queryset(response_data)
        if page is not None:
            return self.get_paginated_response(page)

        return Response(response_data)




class CS_Activity_ViewSet(viewsets.ModelViewSet):
    MODEL = CS_Activity
    queryset = MODEL.objects.all()
    serializer_class = CS_Activity_Serializer

    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =['현장명','불만요청사항','고객명'] 
    filterset_class =  customfilters.CS_Activity_FilterSet

    def get_queryset(self):       
        return self.MODEL.objects.order_by('-id').select_related(
                'claim_fk'
            ).prefetch_related(
                'cs_activity_file_set'  # CS_Activity_File과의 관계 최적화
            )
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)
        # Claim_File에 해당하는 파일들을 저장
        activity_files = request.FILES.getlist('activity_files')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        for file in activity_files:
            CS_Activity_File.objects.create(activity_fk=instance, file=file)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True )
        instance = self.get_object()
        activity_files = request.FILES.getlist('activity_files')
        existing_file_ids:list[int] = request.data.getlist('activity_files_ids', [])
        print ( 'existing_file_ids : ', existing_file_ids )
        print ( request.data )

        # 기존 파일 삭제
        CS_Activity_File.objects.filter(activity_fk=instance).exclude(id__in=existing_file_ids).delete()

        # 새로운 파일 추가
        for file in activity_files:
            CS_Activity_File.objects.create(activity_fk=instance, file=file)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class CS_Claim_File_ViewSet(viewsets.ModelViewSet):
    MODEL = CS_Claim_File
    queryset = MODEL.objects.all()
    serializer_class = CS_Claim_File_Serializer 
    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    filterset_class =  customfilters.CS_Claim_File_FilterSet

class CS_Activity_File_ViewSet(viewsets.ModelViewSet):
    MODEL = CS_Activity_File
    queryset = MODEL.objects.all()
    serializer_class = CS_Activity_File_Serializer 

    parser_classes = [MultiPartParser,FormParser]
    filter_backends = [
           SearchFilter, 
           filters.DjangoFilterBackend,
        ]
    search_fields =[] 
    filterset_class =  customfilters.CS_Claim_File_FilterSet






