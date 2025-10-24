"""
Views for 차량관리_V2 APIs
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
### https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
from django.forms.models import model_to_dict
from django.db.models import Count, Sum , functions, Q, QuerySet
from django.db import transaction
import os
import json
import copy
import pandas as pd
import numpy as np

from . import  models, serializers
from users.models import Api_App권한, Api_App권한_User_M2M
import 차량관리.models as old_models
from users.models import User
from util.base_model_viewset import BaseModelViewSet
from util.trigger_ws_redis_pub import trigger_ws_redis_pub

import json
import logging, traceback
logger = logging.getLogger('차량관리_V2')

class 차량관리_V2_DB_Migrate_API_View(APIView):

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
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': str(e)})

    def clear_new_db(self):
        models.차량관리_기준정보.objects.all().delete()
        models.차량관리_사용자.objects.all().delete()
        models.차량관리_운행DB.objects.all().delete()

    def migration(self) -> dict:
        msg = {}
        # 1. 기준정보: 차량번호 기준 유일한 차량 정보 마이그레이션
        unique_numbers = (
            old_models.차량관리_기준정보.objects
            .exclude(차량번호__isnull=True)
            .exclude(차량번호='')
            .values_list('차량번호', flat=True)
            .distinct()
        )

        map_차량번호_to_new_obj = {}
        for 번호 in unique_numbers:
            old_obj = (
                old_models.차량관리_기준정보.objects
                .filter(차량번호=번호)
                .first()
            )
            if old_obj:
                new_obj = models.차량관리_기준정보.objects.create(
                    법인명=old_obj.법인명,
                    차종=old_obj.차종,
                    차량번호=old_obj.차량번호,
                    타이어규격=old_obj.타이어규격,
                    공급업체=old_obj.공급업체,
                    차량가격=old_obj.차량가격,
                    보증금=old_obj.보증금,
                    대여료_VAT포함=old_obj.대여료_VAT포함,
                    약정운행거리=old_obj.약정운행거리,
                    초과거리부담금=old_obj.초과거리부담금,
                    시작일=old_obj.시작일,
                    종료일=old_obj.종료일,
                    is_exist=True,
                )

                map_차량번호_to_new_obj[old_obj.차량번호] = new_obj
        msg['차량번호_마이그레이션'] = len(unique_numbers)
        
        ### 2. 사용자
        created_users = 0
        for obj in old_models.차량관리_기준정보.objects.all():
            if models.차량관리_사용자.objects.filter(
                차량관리_기준정보_fk=map_차량번호_to_new_obj[obj.차량번호],
                user_fk=obj.user_fk
            ).exists():
                continue
            models.차량관리_사용자.objects.create(
                user_fk=obj.user_fk,
                차량관리_기준정보_fk = map_차량번호_to_new_obj[obj.차량번호]
            )
            created_users += 1
        msg['사용자_마이그레이션'] = created_users
        ### 3. 운행DB
        created_운행DB = 0
        for obj in old_models.차량관리_운행DB.objects.all():
            차량번호_obj = getattr(obj, '차량번호_fk', None)
            car = map_차량번호_to_new_obj.get(차량번호_obj.차량번호) if 차량번호_obj else None
            if not car:
                continue

            if models.차량관리_운행DB.objects.filter(
                일자 = obj.일자,                
                차량번호_fk = car,
                주행거리 = obj.주행거리,
                정비금액 = obj.정비금액,
                정비사항 = obj.정비사항,
                비고 = obj.비고,
                관련근거 = obj.관련근거,
                담당자_snapshot = obj.담당자
            ).exists():
                continue

            담당자_fk = User.objects.filter(user_성명=obj.담당자).first()
            models.차량관리_운행DB.objects.create(
                차량번호_fk = car,
                일자 = obj.일자,
                주행거리 = obj.주행거리,
                정비금액 = obj.정비금액,
                정비사항 = obj.정비사항,
                비고 = obj.비고,
                관련근거 = obj.관련근거,
                담당자_snapshot = obj.담당자,
                담당자_fk = 담당자_fk
            )
            created_운행DB += 1
        msg['운행DB_마이그레이션'] = created_운행DB

        return msg

class 차량관리_V2_기준정보_ViewSet(BaseModelViewSet):
    MODEL = models.차량관리_기준정보
    use_cache = False
    queryset = MODEL.objects.all()
    parser_classes = [ JSONParser, MultiPartParser, FormParser]
    search_fields = ['차량번호']
    ordering_fields = ['차량번호']
    ordering = ['차량번호']
    serializer_class = serializers.차량관리_기준정보_Serializer

    def get_queryset(self):
        return self.MODEL.objects.all()
    
    def update(self, request, *args, **kwargs):
        print(f"request.data: {request.data}")
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"update 오류: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


    @action(detail=False, methods=['post'], url_path='사용자_M2M_Bulk')
    def 사용자_M2M_Bulk(self, request, *args, **kwargs):
        """ 1. 사용자 추가 및 삭제
            2. Api_App권한_User_M2M 에 차량관리_사용자 추가 및 삭제
        """
        try:
            ### added : app_id, user_id
            ### removed : db id이다.
            logger.info(f"request.data: {request.data}")
            app_id = request.data.get('app_id', None)
            added = request.data.get('added', [])
            removed = request.data.get('removed', [])
            
            # 변수 미리 초기화
            bulk_create_list = []
            
            # 문자열로 전달된 경우 JSON으로 파싱
            M2M_model = models.차량관리_사용자
            if added:
                added = json.loads(added) if isinstance(added, str) else added
                if added:
                    # 한 번의 쿼리로 이미 존재하는 관계 확인
                    existing_relations = set(M2M_model.objects.filter(
                        차량관리_기준정보_fk_id=app_id, 
                        user_fk_id__in=added
                    ).values_list('user_fk_id', flat=True))
                    
                    # 존재하지 않는 관계만 생성
                    bulk_create_list = [
                        M2M_model(차량관리_기준정보_fk_id=app_id, user_fk_id=user_id)
                        for user_id in added if user_id not in existing_relations
                    ]
            
            if removed:
                removed = json.loads(removed) if isinstance(removed, str) else removed
            
            with transaction.atomic():           
                #### 1 . 차량관리_사용자 추가 및 삭제          
                if bulk_create_list:
                    M2M_model.objects.bulk_create(bulk_create_list)
                    logger.info(f"{len(bulk_create_list)}개 항목 추가됨")
                
                if removed:
                    deleted_count = M2M_model.objects.filter(
                        user_fk_id__in=removed
                    ).delete()[0]
                    logger.info(f"{deleted_count}개 항목 삭제됨")
                
                #### 2. Api_App권한_User_M2M 에 차량관리_사용자 추가 및 삭제 ✅ 전체적으로 UPDATE함.
                권한_instance = Api_App권한.objects.get(div='차량관리_V2', name='운행관리_사용자')
                qs_사용자 = M2M_model.objects.all()
                
                사용자_id_list = []
                for 사용자 in qs_사용자:
                    _inst, _created = Api_App권한_User_M2M.objects.get_or_create(
                        app_권한=권한_instance,
                        user=사용자.user_fk,
                    )
                    사용자_id_list.append(사용자.user_fk_id)
                ### 제외된 id 삭제
                qs = Api_App권한_User_M2M.objects.filter(app_권한=권한_instance)
                삭제할_qs = qs.exclude(user_id__in=사용자_id_list).exclude(user_id=1)
                if 삭제할_qs.count() > 0:   
                    print( '삭제할 qs 수 : ',삭제할_qs.count() , '삭제할 qs : ',삭제할_qs.all() )
                    삭제할_qs.delete()
                    trigger_ws_redis_pub(handle_name='app_권한')


            # logger.info(f"사용자_id_list: {사용자_id_list}")
            app_instance = models.차량관리_기준정보.objects.get(id=int(app_id))            
            app_data = serializers.차량관리_기준정보_Serializer(app_instance).data
            return Response(data=app_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"bulk_generate 오류: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class 차량관리_V2_운행DB_Base_ViewSet(BaseModelViewSet):
    MODEL = models.차량관리_운행DB
    use_cache = False
    queryset = MODEL.objects.all()
    parser_classes = [ JSONParser, MultiPartParser, FormParser]
    
    filterset_fields = ['차량번호_fk']
    search_fields = ['차량번호_fk__차량번호']
    ordering_fields = ['일자','차량번호_fk__차량번호']
    ordering = ['-일자','차량번호_fk__차량번호']
    serializer_class = serializers.차량관리_운행DB_Serializer

    _type = '관리자'  # 하위에서 override

    def get_queryset(self):
        if self._type == '사용자':
            return self.MODEL.objects.all() #### filterset 이 차량번호_fk 이므로, 해당 차량은 담당자_fk 무관하게 전부 조회됨.
        return self.MODEL.objects.all()
    
    @action(detail=False, methods=['get'], url_path='템플릿')
    def 템플릿(self, request, *args, **kwargs):
        차량번호_fk = request.query_params.get('차량번호_fk')
        try:
            차량 = models.차량관리_기준정보.objects.get(id=차량번호_fk)
        except models.차량관리_기준정보.DoesNotExist:
            return Response({'detail': '차량이 존재하지 않습니다.'}, status=400)

        # 1. 운행DB 모델을 메모리상에서 "가짜 인스턴스"로 만듦
        임시_운행 = models.차량관리_운행DB(
            차량번호_fk=차량,
            일자=datetime.now(),
            주행거리=0,
            정비금액=0,
            정비사항='',
            비고='',
            관련근거='',
            담당자_snapshot= request.user.user_성명,
            담당자_fk=request.user,
        )
        # 2. serializer로 감쌈 (instance 기반)
        serializer = self.get_serializer(임시_운행)
        data = serializer.data
        data['id'] = -9999
        return Response( [data] )
    
    @action(detail=False, methods=['get'], url_path='사용자별_차량_리스트')
    def 사용자별_차량_리스트(self, request, *args, **kwargs):
        user_id = request.user.id
        if self._type == '관리자':
            qs = models.차량관리_기준정보.objects.filter(is_exist=True)
            result = [
                {'차량번호_fk': item.id, '차량번호': item.차량번호}
                for item in qs
            ]
        else:
            qs = (
                models.차량관리_사용자.objects
                .filter(user_fk_id=user_id)
                .select_related('차량관리_기준정보_fk')
            )
            result = [
                {
                    '차량번호_fk': item.차량관리_기준정보_fk.id,
                    '차량번호': item.차량관리_기준정보_fk.차량번호
                }
                for item in qs if item.차량관리_기준정보_fk
            ]

        return Response(result)


class 차량관리_V2_운행DB_관리자_ViewSet(차량관리_V2_운행DB_Base_ViewSet):
    _type = '관리자'

    
class 차량관리_V2_운행DB_사용자_ViewSet(차량관리_V2_운행DB_Base_ViewSet):
    _type = '사용자'

class 차량관리_V2_운행DB_조회_ViewSet(차량관리_V2_운행DB_Base_ViewSet):
    http_method_names = ['get', 'head', 'options']
    