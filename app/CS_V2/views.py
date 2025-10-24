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
from rest_framework.parsers import MultiPartParser,FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.utils import timezone
from datetime import datetime, date,time, timedelta
from django.shortcuts import get_object_or_404

from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date

import util.utils_func as Util
import util.cache_manager as CacheManager

import 품질경영.models as old_models
import 품질경영.serializers as old_serializers
import CS_V2.models as models
import CS_V2.serializers as serializers
# from . import customfilters
from util.base_model_viewset import BaseModelViewSet

import traceback

class Migrate_old_to_new_APIView(APIView):

    def clear_new_db(self):
        models.CS_Activity_File.objects.all().delete()
        models.CS_Claim_File.objects.all().delete()
        models.CS_Activity.objects.all().delete()
        models.CS_Claim.objects.all().delete()

    def get(self, request, format=None):
        try:

            params = request.query_params
            if params.get('action') == 'migrate' :
                with transaction.atomic():
                    msg = self.migration()
                return Response(status=status.HTTP_200_OK, data=msg)
            elif params.get('action') == 'clear' :
                with transaction.atomic():
                    self.clear_new_db()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'action 파라미터가 필요합니다.'})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})
    
    def random_days(self, min:int=-2, max:int=2) -> int:
        import random
        return random.randint(min, max)
    


    def get_conversion_by_진행현황(self, obj:dict) -> dict:
        def get_default_day( obj, field_name, default ):
            field_value = obj.get(field_name, None)
            if field_value is None:
                return default
            return field_value
        
        import copy
        copyed = copy.deepcopy(obj)
        from users.models import User
        old_진행현황 = obj.get('진행현황', None)
        copyed['등록자'] = User.objects.get(id=obj.get('등록자_fk_id')).user_성명
        match old_진행현황:
            case '작성':
                등록일 = obj.get('등록일')
                등록일_date = 등록일.date()
                copyed['진행현황'] = '작성'
                if obj.get('완료요청일') is None or obj.get('완료요청일') == '':
                    copyed['완료요청일'] = 등록일_date + timedelta(days=7)
                else:
                    copyed['완료요청일'] = obj.get('완료요청일')
                return copyed
            case 'Open':
                등록일 = obj.get('등록일')
                등록일_date = 등록일.date()
                완료요청일 = get_default_day( obj, '완료요청일', 등록일_date + timedelta(days=7)) 
                print ('등록일_date : ', 등록일_date, '완료요청일 : ', 완료요청일 )
                copyed['완료요청일'] = 완료요청일
                copyed['진행현황'] = '접수'
                copyed['접수일'] = 등록일 + timedelta(days=self.random_days(min=0, max=2))
                copyed['완료목표일'] = get_default_day( obj, '완료목표일', 완료요청일 + timedelta(days = self.random_days()) )
                copyed['접수자_fk'] = User.objects.get(user_성명='양영모')
                copyed['접수자'] = "양영모"
                copyed['진행계획'] = f" 1. 현상 및 원인 파악 후,\n 2. 시급성 및 중요도를 파악하여 \n 3. 최대한 조속히 처리 예정 \n"
                return copyed
            case 'Close':
                등록일 = obj.get('등록일')
                등록일_date = 등록일.date()
                완료요청일 = get_default_day( obj, '완료요청일', 등록일_date + timedelta(days=7)) 
                print ('등록일_date : ', 등록일_date, '완료요청일 : ', 완료요청일 )
                copyed['완료요청일'] = 완료요청일
                copyed['진행현황'] = '완료'
                copyed['완료목표일'] = get_default_day( obj, '완료목표일', 완료요청일 ) + timedelta(days = self.random_days())
                copyed['접수자_fk'] = User.objects.get(user_성명='양영모')
                copyed['접수자'] = "양영모"
                copyed['접수일'] = 등록일 + timedelta(days=self.random_days(min=0, max=2))
                copyed['진행계획'] = f" 1. 현상 및 원인 파악 후,\n 2. 시급성 및 중요도를 파악하여 \n 3. 최대한 조속히 처리 예정 \n"
                copyed['완료자_fk'] = User.objects.get(user_성명='양영모')
                copyed['완료자'] = "양영모"
                copyed['완료일'] = obj.get('완료일')
                return copyed
            

    def migration(self):
        try:
            with transaction.atomic():
                self.clear_new_db()

                map_old_to_new_claim = {}
                for old_claim in old_models.CS_Claim.objects.all():
                    old_data = old_claim.__dict__.copy()
                    old_data.pop('_state', None)
                    old_id = old_data.pop('id')
                    new_claim = models.CS_Claim.objects.create(**self.get_conversion_by_진행현황(old_data))
                    map_old_to_new_claim[old_id] = new_claim.id

                # Claim File
                for old_id, new_id in map_old_to_new_claim.items():
                    old_files = old_models.CS_Claim_File.objects.filter(claim_fk_id=old_id)
                    new_files = []
                    for old_file in old_files:
                        models.CS_Claim_File.objects.create(
                            claim_fk_id=new_id,
                            file=old_file.file
                        )


                # Activity
                map_old_to_new_activity = {}
                for old_id, new_id in map_old_to_new_claim.items():
                    activities = old_models.CS_Activity.objects.filter(claim_fk=old_id)
                    for old_act in activities:
                        act_data = old_act.__dict__.copy()
                        act_data.pop('_state', None)
                        act_data.pop('id', None)
                        act_data.pop('예정_시작일', None)
                        act_data.pop('예정_완료일', None)
                        act_data['claim_fk_id'] = new_id
                        new_act = models.CS_Activity.objects.create(**act_data)
                        map_old_to_new_activity[old_act.id] = new_act.id

                # Activity File
                for old_id, new_id in map_old_to_new_activity.items():
                    old_files = old_models.CS_Activity_File.objects.filter(activity_fk=old_id)
                    new_files = []
                    for old_file in old_files:
                        models.CS_Activity_File.objects.create(
                            activity_fk_id=new_id,
                            file=old_file.file
                        )

            return {'msg': '마이그레이션 완료'}
        except Exception as e:
            return {'error': f"{str(e)}\n{traceback.format_exc()}"}
        
class CS_Claim_ViewSet(BaseModelViewSet):
    APP_ID = 230
    APP_INFO = {'div':'CS_V2', 'name':'CS관리'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    MODEL = models.CS_Claim    
    queryset = MODEL.objects.all()
    use_cache = False
    cache_base = 'CS_Claim'
    cache_timeout = 60*60*1
    serializer_class = serializers.CS_Claim_Serializer
    parser_classes = [ JSONParser, MultiPartParser, FormParser]
    search_fields = ['현장명','현장주소','Elevator사','부적합유형','고객명','고객연락처']
    ordering_fields = ['등록일','완료일','id']
    ordering = ['-등록일','-완료일','-id']

    def get_queryset(self):
        return self.MODEL.objects.select_related(
                '등록자_fk','el_info_fk','완료자_fk'
                ).prefetch_related(
                    'CS_Activity_set__CS_Activity_File_set',    # CS_Activity와 CS_Activity_File까지 최적화
                    'CS_Claim_File_set'                         # CS_Claim_File과의 관계 최적화
                ).order_by(*self.ordering)
        
    def _get_default_완료요청일(self):
        return timezone.now().date() + timedelta(days=7)
    
    def _perform_create(self, serializer):
        완료요청일 = serializer.validated_data.get('완료요청일', self._get_default_완료요청일())
        진행현황 = serializer.validated_data.get('진행현황', '작성')
        serializer.save(등록자=self.request.user.user_성명, 등록자_fk=self.request.user,
                        등록일 = timezone.now(), 완료요청일=완료요청일, 진행현황=진행현황 )
        return serializer.data
   


    @action(detail=False, methods=['get'], url_path='get_Elevator사')
    def get_Elevator사(self, request):
        """ 엘러베이터 회사 목록 조회 """
        if self.use_cache:
            cache_key = f'{self.cache_base}:Elevator사'
            cached_data = CacheManager.get_cache(cache_key)
            if cached_data:
                print ( 'cache hit : cache_key : ', cache_key )
                return Response(cached_data)
        else:
            self.invalidate_cache()
        
        # 기본값 설정
        default_companies = ['현대', 'OTIS', 'TKE']
        
        # queryset에서 Elevator사 필드의 고유한 값 가져오기
        elevator_companies = self.MODEL.objects.values_list('Elevator사', flat=True).distinct()
        
        # 기본값을 먼저 추가하고, 기본값에 없는 엘리베이터 회사들을 추가
        combined_companies = default_companies + [company for company in elevator_companies if company and company not in default_companies]
        if self.use_cache:
            CacheManager.set_cache(cache_key, combined_companies, self.cache_timeout)
        print ( f'cache useful : {self.use_cache} cache miss : cache_key : ', cache_key )
        return Response(combined_companies)
    
    @action(detail=False, methods=['get'], url_path='get_부적합유형')
    def get_부적합유형(self, request):
        """ 부적합유형 목록 조회 """
        if self.use_cache:
            cache_key = f'{self.cache_base}:부적합유형'
            cached_data = CacheManager.get_cache(cache_key)
            if cached_data:
                print ( 'cache hit : cache_key : ', cache_key )
                return Response(cached_data)
        else:
            self.invalidate_cache()
        
        # 기본값 설정
        default_types = ['스크래치','이색',]
        
        # queryset에서 불량유형 필드의 고유한 값 가져오기
        types = self.MODEL.objects.values_list('부적합유형', flat=True).distinct()
        
        # 기본값을 먼저 추가하고, 기본값에 없는 불량유형들을 추가
        combined_types = default_types + [type for type in types if type and type not in default_types]
        if self.use_cache:
            CacheManager.set_cache(cache_key, combined_types, self.cache_timeout)
        print ( f'cache useful : {self.use_cache} cache miss : cache_key : ', cache_key )
        return Response(combined_types)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print (' view create내 ', request.data)
        # Claim_File에 해당하는 파일들을 저장
        claim_files = request.FILES.getlist('claim_files')
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("🔴 serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # ✅ base의 perform_create 호출 (invalidate_cache 포함)
        self.perform_create(serializer)
        instance = serializer.instance  # or return value from _perform_create
        # 🔧 claim_files 저장
        for file in claim_files:
            models.CS_Claim_File.objects.create(claim_fk=instance, file=file)
        
        #### save 후, refresh ( claim_files update 후, )
        serializer = self.get_serializer(instance)        

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
                models.CS_Claim_File.objects.filter(claim_fk=instance).delete()
            else:
                # 기존 파일 삭제
                models.CS_Claim_File.objects.filter(claim_fk=instance).exclude(id__in=existing_file_ids).delete()
            
            print ( 'existing_file_ids : ', existing_file_ids )

        # 새로운 파일 추가
        new_files = [
            models.CS_Claim_File(claim_fk=instance, file=file)
            for file in claim_files
        ]
        models.CS_Claim_File.objects.bulk_create(new_files)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 업데이트된 인스턴스를 다시 조회하여 직렬화
        updated_instance = self.MODEL.objects.get(id=instance.id)   
        updated_serializer = self.get_serializer(updated_instance)

        return Response(updated_serializer.data)
    
    @transaction.atomic
    @action(detail=True, methods=['patch'], url_path='update_진행현황')
    def update_진행현황(self, request, pk=None):
        instance = self.get_object()
        print ( 'update_진행현황내 ', request.data )

        # query_params에서 상태값 받기
        진행현황 = request.data.get('진행현황', None)
        if 진행현황 is None:
            return Response({"detail": "진행현황 파라미터가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        if 진행현황 not in ['의뢰', '접수', '완료', '반려']:
            return Response({"detail": f" 요청 진행현황 :{진행현황} ==> '의뢰', '접수', '완료', '반려' 여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = {'진행현황':진행현황 }
        match 진행현황:
            case '의뢰':
                data.update( { '등록일': timezone.now()} )
            case '접수':
                # 완료요청일은 CS 등록 시 필수이며, 접수 시에는 request로 수정 가능
                완료목표일 = request.data.get('완료목표일', instance.완료요청일)
                진행계획 = request.data.get('진행계획', '')
                data.update( { '접수일': timezone.now() , '완료목표일':완료목표일, 
                              '접수자':self.request.user.user_성명, '접수자_fk':self.request.user.id,
                              '진행계획':진행계획} )
                print ( 'data : ', data )
            case '완료':
                data.update( { '완료일': timezone.now(), '완료자':self.request.user.user_성명, '완료자_fk':self.request.user.id} )
            case '반려':
                반려사유 = request.data.get('반려사유', '')
                data.update( { '접수일': timezone.now() , 
                              '접수자':self.request.user.user_성명, '접수자_fk':self.request.user.id,
                              '반려사유':반려사유} )

        serializer = self.get_serializer(instance, data=data, partial=True)
        if not serializer.is_valid():
            print("🔴 serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

    # @action(detail=True, methods=['get'], url_path='activities')
    # def get_activities(self, request, pk=None):
    #     claim = self.get_object()
    #     activities = claim.cs_activity_set.all().order_by('-등록일')
    #     serializer = serializers.CS_Activity_Serializer(activities, many=True)
    #     return Response(serializer.data)

    # @action(detail=True, methods=['post'], url_path='add-activity')
    # def add_activity(self, request, pk=None):
    #     claim = self.get_object()
    #     data = request.data.copy()
    #     data['claim_fk'] = claim.id
    #     serializer = serializers.CS_Activity_Serializer(data=data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     self.invalidate_cache()

    #     claim_serializer = self.get_serializer(claim)
    #     return Response(claim_serializer.data, status=201)

    # @action(detail=True, methods=['patch'], url_path='edit-activity/(?P<activity_id>[^/.]+)')
    # def edit_activity(self, request, pk=None, activity_id=None):
    #     claim = self.get_object()
    #     activity = get_object_or_404(models.CS_Activity, pk=activity_id, claim_fk=pk)
    #     serializer = serializers.CS_Activity_Serializer(activity, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     self.invalidate_cache()

    #     claim_serializer = self.get_serializer(claim)
    #     return Response(claim_serializer.data)

    # @action(detail=True, methods=['delete'], url_path='delete-activity/(?P<activity_id>[^/.]+)')
    # def delete_activity(self, request, pk=None, activity_id=None):
    #     claim = self.get_object()
    #     activity = get_object_or_404(models.CS_Activity, pk=activity_id, claim_fk=pk)
    #     activity.delete()
    #     self.invalidate_cache()

    #     claim_serializer = self.get_serializer(claim)
    #     return Response(claim_serializer.data)


class CS_Claim_등록_ViewSet(CS_Claim_ViewSet):
    APP_ID = 236
    APP_INFO = {'div':'CS_V2', 'name':'CS등록'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    use_cache = False
    cache_base = 'CS_Claim_등록'
    cache_timeout = 60*60*1

    def get_queryset(self):
        return self.MODEL.objects.select_related(
                '등록자_fk','el_info_fk','완료자_fk'
                ).prefetch_related(
                    'CS_Activity_set__CS_Activity_File_set',    # CS_Activity와 CS_Activity_File까지 최적화
                    'CS_Claim_File_set'                         # CS_Claim_File과의 관계 최적화
                ).order_by(*self.ordering).filter(진행현황='작성', 등록자_fk=self.request.user)


class CS_Claim_활동_ViewSet(CS_Claim_ViewSet):
    APP_ID = 237
    APP_INFO = {'div':'CS_V2', 'name':'CS활동'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    use_cache = True
    cache_base = 'CS_Claim_활동'
    cache_timeout = 60*60*1

    def get_queryset(self):
        return  ( self.MODEL.objects.select_related('등록자_fk').prefetch_related('CS_Activity_set')
                 .order_by(*self.ordering).filter(진행현황='Open') )
    



class CS_Activity_ViewSet(BaseModelViewSet):
    """ CS_Activity MODEL 관리
        현재 25-8-1 기준, Client는 create만 가능함.
    """
    APP_ID = 238
    APP_INFO = {'div':'CS_V2', 'name':'CS활동'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    MODEL = models.CS_Activity
    queryset = MODEL.objects.all()
    serializer_class = serializers.CS_Activity_Serializer
    parser_classes = [ MultiPartParser, FormParser]
    ordering_fields = ['등록일','id']
    ordering = ['-등록일','-id']

    use_cache = True
    cache_base = 'CS_Activity'
    cache_timeout = 60*60*1

    def _perform_create(self, serializer):
        활동일 = serializer.validated_data.get('활동일', timezone.now())
        등록일 = timezone.now()
        등록자_fk_id = self.request.user.id
        serializer.save(활동일=활동일, 등록자_fk_id=등록자_fk_id, 등록일=등록일 )
        self.erase_관련_cache()
        return serializer.data
    
    def _perform_update(self, serializer):
        serializer.save()
        self.erase_관련_cache()
        return serializer.data

    def _perform_delete(self, instance):
        instance.delete()
        self.erase_관련_cache()

    def erase_관련_cache(self):
        CacheManager.clear_all_cache(base='CS_Claim')

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
        if not serializer.is_valid():
            print("🔴 serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        instance = serializer.instance  # or return value from _perform_create
        for file in activity_files:
            models.CS_Activity_File.objects.create(activity_fk=instance, file=file)

        #### save 후, refresh ( claim_files update 후, )
        serializer = self.get_serializer(instance) 

        return Response(serializer.data, status=status.HTTP_201_CREATED)