"""
Views for the config APIs
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
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.conf import settings
# from datetime import datetime, date,time, timedelta
import datetime
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
import redis
from django.core.cache import cache
from util.redis_publisher import RedisPublisher
from config.models import WS_URLS_DB


from . import serializers as Config_Serializers
from . import models as Config_Models
from . import customfilters
from util import utils_func as Utils
from util.trigger_ws_redis_pub import trigger_ws_redis_pub
from util.base_model_viewset import BaseModelViewSet
from shapi.setting_log import setup_logging
import logging, traceback
logger = logging.getLogger(__name__)

import util.utils_func as Util
import util.cache_manager as CacheManager

class WS_URLS_DB_ViewSet(BaseModelViewSet):
    APP_ID = 239
    APP_INFO = {'div':'config', 'name':'WS_URLS관리'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    MODEL = Config_Models.WS_URLS_DB
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.WS_URLS_DB_Serializer

    parser_classes = [ MultiPartParser, FormParser]
    search_fields = ['group','channel','name']
    ordering_fields = ['group','channel','name']
    ordering = ['group','channel','name']

    use_cache = True
    cache_base = 'WS_URLS_DB'
    cache_timeout = 60*60*1

    def _perform_create(self, serializer):
        self.invalidate_cache()
        CacheManager.clear_ws_url_db_all()
        serializer.save()

    def _perform_update(self, serializer):
        self.invalidate_cache()
        CacheManager.clear_ws_url_db_all()
        serializer.save()

    def _perform_destroy(self, instance):
        self.invalidate_cache()
        CacheManager.clear_ws_url_db_all()
        instance.delete()

    def get_queryset(self):
        return self.MODEL.objects.order_by(*self.ordering)
    
    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request, *args, **kwargs):
        data = self.get_template_data()       
        return Response(status=status.HTTP_200_OK, data= data )

    
   


class Table_Config_ViewSet(viewsets.ModelViewSet):
    MODEL = Config_Models.Table_Config
    div, name = 'Config', 'Table설정'
    # TABLE_NAME = f"{div}_{name}_appID_{Utils.get_tableName_from_api권한(div=div, name=name)}"
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.Table_Config_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['table__table_name'] 
    filterset_class = customfilters.Table_Config_Filter
    ordering_fields = ['table__table_name', 'order']
    ordering = ['table__table_name', 'order']

    handle_name = 'table_total_config'
    # Utils.generate_table_config_db( 
    #     table_name=TABLE_NAME, 
    #     model_field = Utils.get_MODEL_field_type(MODEL),
    #     serializer_field = Utils.get_Serializer_field_type( Config_Serializers.Table_Config_Serializer() ),
    # )

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    @action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
    def request_ws_redis_publish(self, request, *args, **kwargs):
        try:
            trigger_ws_redis_pub(handle_name='table_total_config')
            return Response(status=status.HTTP_200_OK, data={'result':'success'})
        except Exception as e:
            data = {'error':str(e)}
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)

    @action(detail=False, methods=['post'], url_path='get_table_list')
    def get_table_list(self, request, *args, **kwargs):
        """
        table_name_list 리스트 형식으로 받아서 해당 테이블 리스트를 반환 ( client app실행시 bg 작업 )
        """
        try:
            # QueryDict에서 getlist 메소드를 사용하여 모든 값을 리스트로 가져옴
            table_name_list = request.data.getlist('table_name_list')
            
            if not table_name_list:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, 
                    data={'error':'table_name_list가 비어있습니다.'})
            
            table_list = self.get_queryset().filter(table_name__in=table_name_list)
            serializer = self.get_serializer(table_list, many=True)
            return Response(status=status.HTTP_200_OK, data={'result':serializer.data})
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"get_table_list 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error':str(e), 'traceback': error_traceback})
        
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request, *args, **kwargs):
        try:
            table_name = request.data.get('table_name', None)
            list_data = json.loads(request.data.get('datas'))

            if not table_name:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'table_name이 없습니다.'})
            if not isinstance(list_data, list) or not list_data:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'datas는 비어있거나 리스트 형식이 아닙니다.'})

            if list_data[0].get('id') and isinstance(list_data[0]['id'], int) and list_data[0]['id'] > 0:
                bulk_update_list = []
                update_fields = [k for k in list_data[0].keys() if k != 'id']
                for data in list_data:
                    table_id = data.pop('table')
                    bulk_update_list.append(self.MODEL(**data, table_id=table_id))
                with transaction.atomic():
                    self.MODEL.objects.bulk_update(bulk_update_list, fields=update_fields)
            else:
                print ( 'create로 시작 ')
                table_obj, _ = Config_Models.Table.objects.get_or_create(table_name=table_name)
                for data in list_data:
                    data['table'] = table_obj
                    data.pop('id', None)
                bulk_create_list = [self.MODEL(**data) for data in list_data]
                with transaction.atomic():
                    #### bulk create 전에 기존 데이터 삭제
                    self.MODEL.objects.filter(table = table_obj).delete()
                    self.MODEL.objects.bulk_create(bulk_create_list)

            # self.trigger_ws_redis_pub(handle_name='table_total_config')
            return Response(status=status.HTTP_200_OK, data={'result': 'success'})

        except Exception as e:
            logger.exception("bulk 처리 중 예외 발생")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': str(e)})

    @action(detail=False, methods=['post',], url_path='bulk_create')
    def bulk_create(self, request, *args, **kwargs):
        try:
            table_name = request.data.get('table_name', None)
            list_data = json.loads(request.data.get('datas'))
            if not isinstance(list_data, list):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':'datas는 리스트 형식이어야 합니다.'})
            table_name = list_data[0].get('table_name', None)
            if not table_name:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':'table_name이 없습니다.'})

                
                table_id = tableInstance.id
            
            # id 제거
            for data in list_data:
                data.pop('id', None)  # 'id' 키가 없을 수도 있으니 안전하게

            # bulk create 
            with transaction.atomic():
                tableInstance, _ = Config_Models.Table.objects.get_or_create(table_name=table_name)
                # 인스턴스 생성
                update_bulk_list = [
                    self.MODEL(**data, table_id=tableInstance.id)
                    for data in list_data
                ]
                self.MODEL.objects.bulk_create(update_bulk_list)

            ### trigger WS REDIS PUB
            # self.trigger_ws_redis_pub(handle_name='table_total_config')

            return Response (
                {'result':'success'},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"bulk_update 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post','put','patch'], url_path='bulk_update')
    def bulk_update(self, request, *args, **kwargs):
        try:
            list_data = json.loads(request.data.get('datas'))
            if not isinstance(list_data, list):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':'datas는 리스트 형식이어야 합니다.'})
            


            instance_list = []
            with transaction.atomic():
                for data in list_data:
                    # ID로 직접 객체를 조회
                    instance = self.MODEL.objects.get(id=data.get('id'))
                    # 데이터로 객체 업데이트
                    for key, value in data.items():
                        if key == 'id':  # id는 업데이트하지 않음
                            continue
                        if key == 'table':
                            setattr(instance, key, Config_Models.Table.objects.get(id=value))
                        else:
                            setattr(instance, key, value)
                    instance.save()
                    instance_list.append(instance)

            # self.trigger_ws_redis_pub(handle_name='table_total_config')

            return Response (
                {'result':'success'},
                status=status.HTTP_200_OK,
            )


        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"bulk_update 중 오류 발생: {e}")
            print(f"상세 오류: {error_traceback}")
            return Response({
                'error': str(e),
                'traceback': error_traceback
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class Cache_ViewSet(viewsets.ViewSet):
    """ 
    캐시 데이터를 조회하고 관리하는 ViewSet
    """
    
    def list(self, request):
        """모든 캐시 키와 값을 반환합니다."""
        try:
            # Django의 캐시 백엔드가 Redis인 경우
            if hasattr(settings, 'CACHES') and settings.CACHES.get('default', {}).get('BACKEND', '').endswith('RedisCache'):
                redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
                raw_keys = redis_client.keys('*')

                    # 키를 디코딩하여 읽기 쉬운 형태로 변환
                decoded_keys = []
                for key in raw_keys:
                    try:
                        decoded_keys.append(key.decode('utf-8'))
                    except UnicodeDecodeError:
                        decoded_keys.append(str(key))
                print (f"decoded_keys: {decoded_keys}")
                
                # 전체 keys 중 가장 길게 split 된 것 기준으로 max_length 결정
                max_parts = max(decoded_keys, key=lambda k: len(k.split(':')), default='').split(':')
                max_len = len(max_parts)

                headers = ['group', 'channel', 'action'] + [f'key{i+1}' for i in range(max_len - 3)]
                cache_list = []
                for key in decoded_keys:
                    parts = key.replace(':1:', '').split(':')
                    cache_data = dict.fromkeys(headers, None)  # 기본 None 채우기
                    for idx, part in enumerate(parts):
                        if idx < len(headers):
                            cache_data[headers[idx]] = part
                    try:
                        size = redis_client.memory_usage(key)
                        cache_data['size(kb)'] = int(size / 1024) if size else 0
                    except Exception as e:
                        cache_data['size(kb)'] = f"값 가져오기 실패: {e}"
                    cache_list.append(cache_data)

                total_size = sum(cd.get('size(kb)', 0) for cd in cache_list if isinstance(cd.get('size(kb)'), int))
                total_dict = dict.fromkeys(headers, '총합')
                total_dict['size(kb)'] = total_size
                cache_list.append(total_dict)
                print (f"cache_list: {cache_list}")
                return Response(status=status.HTTP_200_OK, data=cache_list)
            else:
                # 다른 캐시 백엔드의 경우 (제한된 기능)
                return Response({
                    'error': '현재 캐시 백엔드는 모든 키 조회를 지원하지 않습니다. Redis 캐시 백엔드를 사용해주세요.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"캐시 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return Response({
                'error': f'캐시 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def keys(self, request):
        """모든 캐시 키 목록과 크기만 반환합니다."""
        try:
            if hasattr(settings, 'CACHES') and settings.CACHES.get('default', {}).get('BACKEND', '').endswith('RedisCache'):
                redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
                all_keys = redis_client.keys('*')
                keys_info = []
                logger.info(f"all_keys: {all_keys}")
                for key in all_keys:
                    key_str = key.decode('utf-8')
                    # 키의 크기(바이트) 가져오기
                    size = redis_client.memory_usage(key)
                    logger.info(f"key: {key_str}, size: {size}")
                    keys_info.append({
                        'key': key_str,
                        'size': size
                    })
                
                return Response({
                    'count': len(keys_info),
                    'keys': keys_info
                })
            else:
                return Response({
                    'error': '현재 캐시 백엔드는 모든 키 조회를 지원하지 않습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'캐시 키를 가져오는 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'], url_path='clear_all')
    def clear_all(self, request):
        """모든 캐시를 삭제합니다."""
        try:
            cache.clear()
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                data = {
                'message': '모든 캐시가 성공적으로 삭제되었습니다.'
            })
        except Exception as e:
            return Response({
                'error': f'캐시를 삭제하는 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='key/(?P<cache_key>[^/.]+)')
    def get_key(self, request, cache_key=None):
        """특정 키의 캐시 값을 조회합니다."""
        try:
            value = cache.get(cache_key)
            if value is None:
                return Response({
                    'error': f'키 "{cache_key}"에 해당하는 캐시가 없습니다.'
                }, status=status.HTTP_404_NOT_FOUND)
                
            return Response({
                'key': cache_key,
                'value': value
            })
        except Exception as e:
            return Response({
                'error': f'캐시 값을 가져오는 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], url_path='key/(?P<cache_key>[^/.]+)')
    def delete_key(self, request, cache_key=None):
        """특정 키의 캐시를 삭제합니다."""
        try:
            cache.delete(cache_key)
            return Response({
                'message': f'키 "{cache_key}"의 캐시가 삭제되었습니다.'
            })
        except Exception as e:
            return Response({
                'error': f'캐시를 삭제하는 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class Resources_ViewSet(viewsets.ModelViewSet):
    MODEL = Config_Models.Resources
    queryset = MODEL.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = Config_Serializers.Resources_Serializer
    filter_backends = [
        SearchFilter, 
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields =['name'] 
    # filterset_class = customfilters.Resources_Filter
    ordering_fields = ['name', 'updated_at']
    ordering = ['name', 'updated_at']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
   
    @action(detail=False, methods=['get'], url_path='login-logo',
            permission_classes=[AllowAny], authentication_classes=[])
    # @permission_classes([AllowAny])
    def login_logo(self, request, *args, **kwargs):
        """ 로그인 로고 이미지 반환 """
        from django.http import HttpResponse
        try:
            cache_key = 'config:resources:login-logo:'
            image_content = cache.get(cache_key)
            if not image_content:
                login_logo = self.MODEL.objects.get(name='login:logo')
                file_path = login_logo.file.path
                with open(file_path, 'rb') as file:
                    image_content = file.read()
                    cache.set(cache_key, image_content, timeout=60*60*24)
            
            return HttpResponse(image_content, content_type='image/jpeg')
        except Exception as e:
            logger.error(f"login_logo 오류 : {e}")
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': str(e)})
    
    @action(detail=False, methods=['get'], url_path='request_ws_redis_publish')
    def request_ws_redis_publish(self, request, *args, **kwargs):
        try:
            trigger_ws_redis_pub(handle_name='table_total_config')
            return Response(status=status.HTTP_200_OK, data={'result':'success'})
        except Exception as e:
            data = {'error':str(e)}
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data= data)
    
    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request, *args, **kwargs):
        """ 템플릿 생성 """
        instance = self.MODEL()
        serializer = self.get_serializer(instance)
        data = serializer.data.copy()
        data['id'] = -1
        data['updated_at'] = datetime.datetime.now().isoformat()

        return Response(status=status.HTTP_200_OK, data= data )
    

class Table_ViewSet(BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.Table
    queryset = MODEL.objects.all()
    search_fields =['table_name'] 
    # filterset_class = customfilters.Table_Menus_Filter
    ordering_fields = ['table_name']
    ordering = ['table_name']
    serializer_class = Config_Serializers.Table_Serializer

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
class Table_Only_Name_ViewSet(viewsets.ModelViewSet):
    MODEL = Config_Models.Table
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.Table_Only_Name_Serializer
    ordering_fields = ['table_name']
    ordering = ['table_name']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )



class V_Header_Menus_ViewSet(BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.V_Header_Menus
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.V_Header_Menus_Serializer
    search_fields =['name'] 
    # filterset_class = customfilters.V_Header_Menus_Filter
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    def list(self, request, *args, **kwargs):
        logger.debug("[V_Header_Menus_ViewSet] list called")
        logger.debug(f"[V_Header_Menus_ViewSet] request: {request}")
        return super().list(request, *args, **kwargs)

class H_Header_Menus_ViewSet(BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.H_Header_Menus
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.H_Header_Menus_Serializer
    search_fields =['name'] 
    # filterset_class = customfilters.V_Header_Menus_Filter
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request, *args, **kwargs):
        """ bulk로 저장"""


class Cell_Menus_ViewSet(BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.Cell_Menus
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.Cell_Menus_Serializer
    search_fields =['name'] 
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )

class Table_link_Bulk_Mixin:
    def bulk_save(self, request, *args, **kwargs):
        """ bulk로 저장"""
        try:
            table_obj, bulk_list = self.bulk_save_list(request, self.MODEL)
            if table_obj and bulk_list:
                with transaction.atomic():
                    self.MODEL.objects.filter(table=table_obj).delete()
                    self.MODEL.objects.bulk_create(bulk_list)
                # self.trigger_ws_redis_pub(handle_name='table_total_config')
                return Response(status=status.HTTP_200_OK, data={'result':'success'})            
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':'ids가 없습니다.'})
        except Exception as e:
            logger.error(f"[Table_link_Bulk_Mixin] bulk 오류 : {e}")
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'error': str(e)})

    def bulk_save_list( self, request, MODEL, *args, **kwargs) -> tuple:
        try:
            table_name = request.data.get('table_name')
            table_obj = Config_Models.Table.objects.get(table_name=table_name)
            menu_ids_raw = request.data.get('ids', [])
            menu_ids = json.loads(menu_ids_raw) if isinstance(menu_ids_raw, str) else menu_ids_raw
            logger.debug(f"[Table_link_Bulk_Mixin] menu_ids: {menu_ids}")

            if menu_ids and isinstance(menu_ids, list):
                bulk_list = [
                    MODEL(table=table_obj, menu_id=menu_dict['id'], order=order)
                    for order, menu_dict in enumerate(menu_ids)
                ]
                return table_obj, bulk_list
            else:
                return None, None
        except Exception as e:
            logger.error(f"[bulk_save] 오류 : {e}")
            logger.error(traceback.format_exc())
            return None, None

class TableVHeaderLink_ViewSet(Table_link_Bulk_Mixin, BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.TableVHeaderLink
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.TableVHeaderLink_Serializer
    search_fields =['table_menu__table_name'] 
    ordering_fields = ['table_menu__table_name', 'order']
    ordering = ['table_menu__table_name', 'order']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request, *args, **kwargs):
        """ bulk로 저장"""
        return self.bulk_save(request, *args, **kwargs)

class TableHHeaderLink_ViewSet( Table_link_Bulk_Mixin, BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.TableHHeaderLink
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.TableHHeaderLink_Serializer
    search_fields =['table_menu__table_name'] 
    ordering_fields = ['table_menu__table_name', 'order']
    ordering = ['table_menu__table_name', 'order']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request, *args, **kwargs):
        """ bulk로 저장"""
        return self.bulk_save(request, *args, **kwargs)



class TableCellMenuLink_ViewSet(BaseModelViewSet):
    APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.TableCellMenuLink
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.TableCellMenuLink_Serializer
    search_fields =['table_menu__table_name'] 
    ordering_fields = ['table_menu__table_name', 'order']
    ordering = ['table_menu__table_name', 'order']

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )

class ColorScheme_ViewSet(BaseModelViewSet):
    # APP_ID = 193 ###  TABLE설정임
    MODEL = Config_Models.ColorScheme
    APP_INFO = {'div':'config', 'name':'color_scheme'}
    APP_INSTANCE = Util.get_app_instance(info=APP_INFO)
    queryset = MODEL.objects.all()
    serializer_class = Config_Serializers.ColorScheme_Serializer
    search_fields =['name'] 
    ordering_fields = ['name']
    ordering = ['name']

    use_cache  = False

    def get_queryset(self):
        return self.MODEL.objects.order_by( *self.ordering )
    
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request, *args, **kwargs):
        """ bulk로 저장"""
        data = request.data.copy()
        excel_datas:list[dict] = json.loads(data.get('excel_datas', '[]')) 
        data.pop('excel_datas')
        with transaction.atomic():
            for row in excel_datas:
                serializer = self.get_serializer(data=row)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        qs = self.get_queryset()    
        serializer = self.get_serializer(qs, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)
