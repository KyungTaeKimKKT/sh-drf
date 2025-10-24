from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Any

from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from django.conf import settings
from django.db import models
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from rest_framework.exceptions import PermissionDenied
from users.models import User, Api_App권한, Api_App권한_User_M2M
from django.core.cache import cache
from rest_framework.response import Response
from urllib.parse import urlencode
from django.urls import resolve, Resolver404
from django.urls.resolvers import _route_to_regex
import time, re
from rest_framework.permissions import AllowAny

from util.cache_manager import set_사용자별_app권한_캐시, get_사용자별_app권한_캐시, delete_사용자별_app권한_캐시
import util.cache_manager as Cache_Manager

import logging
logger = logging.getLogger(__name__)

class DBViewPermissionMixin:
    APP_INSTANCE:Optional[Api_App권한] = None

    def is_permission_use_cache(self) -> bool:
        if hasattr(self, 'use_cache_permission'):
            return self.use_cache_permission
        elif hasattr(self, 'USE_CACHE_PERMISSION'):
            return self.USE_CACHE_PERMISSION
        return False

    def initial(self, request, *args, **kwargs):
        """
        DRF lifecycle hook - user is authenticated at this point.
        """
        super().initial(request, *args, **kwargs)  # 이걸 먼저 호출해야 `request.user` 설정됨
        logger.info(f"AUTH DEBUG - request.user: {request.user}")
        logger.info(f"AUTH DEBUG - request.auth: {request.auth}")
        logger.info(f"AUTH DEBUG - AUTH HEADER: {request.META.get('HTTP_AUTHORIZATION')}")

        user = request.user
        if not user.is_authenticated:
            if any(isinstance(p, AllowAny) for p in self.get_permissions()):
                # AllowAny 이면 permission check skip
                return
            raise PermissionDenied("인증이 필요합니다.")

        if user.is_admin:
            return True
        permission = False
        if self.APP_INSTANCE is None:
            return 
        try:
            if self.is_permission_use_cache():
                start_time = time.time()    
                user_pks = get_사용자별_app권한_캐시(app_instance=self.APP_INSTANCE)     
                logger.info(f"[DBViewPermissionMixin] user_pks: {user_pks}")
                if user_pks:                
                    permission = bool(user.id in user_pks)
                else:
                    set_사용자별_app권한_캐시()
                    user_pks = get_사용자별_app권한_캐시(app_instance=self.APP_INSTANCE)
                    logger.info(f"[DBViewPermissionMixin] user_pks: {user_pks}")
                    if user_pks:                    
                        permission = bool(user.id in user_pks)
                    else:
                        permission = False

                end_time = time.time()
                print(f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec")
                
                if permission:
                    return True
                else:
                    logger.info(f"[DBViewPermissionMixin] {self.APP_ID} {user}접근 권한이 없습니다.")
                    raise PermissionDenied("접근 권한이 없습니다.")
            else:
                ### not use cache
                from users.models import Api_App권한_User_M2M, Api_App권한
                return Api_App권한_User_M2M.objects.filter(
                    user=user, 
                    app_권한=self.APP_INSTANCE
                    ).exists()
        except Exception as e:
            logger.info(f"[DBViewPermissionMixin] {self.APP_ID} {user} 권한 확인 실패: {e}")
            raise PermissionDenied("권한 확인 실패")
        
class CacheMixin:

    def get_cache_key(self, request, *args, **kwargs) -> Optional[str]:
        if not self.cache_base:
            logger.warning(f"[CacheMixin] cache_base 없음 : {self.APP_ID}")
            return None
        path = request.path
        query_string = urlencode ( sorted(request.query_params.items()) )
        
        cache_key = f"{self.get_cache_base_appended()}:{path.replace('/', ':').strip(':')}:{query_string.replace('?','')}"
        return cache_key
    
    def get_cache_base_appended(self) -> str:
        if not self.cache_base:
            logger.warning(f"[CacheMixin] cache_base 없음 : {self.APP_ID}")
            return None
        return f"DRF:{self.cache_base}"
    
    def is_cache_mode(self) -> bool:
        if hasattr(self, 'use_cache'):
            return self.use_cache
        elif hasattr(self, 'USE_CACHE'):
            return self.USE_CACHE
        return False

    def list(self, request, *args, **kwargs):
        logger.debug(f"[CacheMixin] list 호출 : {self.is_cache_mode()}")
        if self.is_cache_mode():
            cache_key = self.get_cache_key(request, *args, **kwargs)
            cached_data = Cache_Manager.get_cache(cache_key)
            if cached_data:
                logger.info(f"[CacheMixin] cache hit : {cache_key}")
                return Response(cached_data)
            response = super().list(request, *args, **kwargs)
            Cache_Manager.set_cache(cache_key, response.data, timeout=self.cache_timeout)
            return response
        else:
            self.invalidate_cache()
        return super().list(request, *args, **kwargs)
    
    def invalidate_cache(self):
        if self.is_cache_mode():
            Cache_Manager.clear_all_cache(self.get_cache_base_appended())

    def perform_create(self, serializer):
        self.invalidate_cache()
        self._perform_create(serializer)

    def _perform_create(self, serializer):
        # 기본 구현: 그냥 저장
        serializer.save()

    def perform_update(self, serializer):
        self.invalidate_cache()
        self._perform_update(serializer)

    def _perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        self.invalidate_cache()
        self._perform_destroy(instance)

    def _perform_destroy(self, instance):
        instance.delete()

from rest_framework.filters import OrderingFilter

class CustomOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)

        if params:
            fields = [param.strip() for param in params.split(',')]
        else:
            fields = getattr(view, 'ordering', [])  # <= 여기!
        if fields:
            return self.remove_invalid_fields(queryset, fields, view, request)
        return fields
    
    def remove_invalid_fields(self, queryset, ordering, view, request):
        if not ordering:
            # ordering 없으면 ViewSet의 ordering으로 강제
            ordering = getattr(view, 'ordering', [])
        return super().remove_invalid_fields(queryset, ordering, view, request)

class BaseModelViewSet(CacheMixin,
                       DBViewPermissionMixin, 
                       viewsets.ModelViewSet):
    """
    BaseModelViewSet is a base class for all model viewsets.
    """
    MODEL:Optional[models.Model] = None
    APP_ID:Optional[int] = None

    # queryset = MODEL.objects.all()
    serializer_class = None
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        # OrderingFilter,
        CustomOrderingFilter
    ]
    search_fields = []
    ordering_fields = []
    ordering = ['-id']  ### 기본 정렬 순서 :상속받은곳에서 override 해야함

    # def dispatch(self, request, *args, **kwargs):
    #     self.check_view_permission(request, *args, **kwargs)
    #     return super().dispatch(request, *args, **kwargs)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print('BASEMODELVIEWSET MRO : ', self.__class__.__mro__)   # 진짜 MRO 체인 확인

    def get_queryset(self):
        """
        get_queryset is a method that returns the queryset for the viewset.
        """
        self.queryset =  self.MODEL.objects.all().order_by( *self.ordering )
        return self.queryset


    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


    def get_template_data(self) -> dict:
        """ model 템플릿 데이터 생성  : data['id'] = -1 로 기본생성함."""
        instance = self.MODEL()
        serializer = self.get_serializer(instance)
        data = serializer.data.copy()
        data['id'] = -1
        return data