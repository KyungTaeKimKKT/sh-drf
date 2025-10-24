from typing import Optional
from django.db.models import Model
from rest_framework import serializers
from functools import wraps
import time, datetime
import uuid
from pathlib import Path
import json
import re
from functools import wraps
from decimal import Decimal
from django.core.exceptions import FieldDoesNotExist
from config import models as Config_Models
import users.models as User_models
import traceback

from rest_framework.routers import DefaultRouter
from django.urls import get_resolver, URLPattern, URLResolver

import logging, traceback
logger = logging.getLogger(__name__)

def print_debug(app_name:str, func_name:str, msg:dict|str|list|tuple|set|int|float|bool|None) -> None:
    """ loki 있는 형식으로 출력합니다. 
    
    Args:
        app_name: 앱 이름
        func_name: 함수 or class 이름
        msg: 메시지
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _dict = {
        "app_name": app_name,
        "func_name": func_name,
        "timestamp": ts,
        "message": msg
    }
    print ( json.dumps(_dict, ensure_ascii=False ) )

def get_app_instance(app_id:Optional[int]=None, info:Optional[dict]=None):
    try:
        if app_id:
            return User_models.Api_App권한.objects.get(pk=app_id)
        elif info:
            return User_models.Api_App권한.objects.get(div=info['div'], name=info['name'])
        else:
            return None
    except User_models.Api_App권한.DoesNotExist:
        return None

def find_viewset_url_pattern(patterns, viewset_cls):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            callback_cls = getattr(getattr(pattern.callback, 'cls', None), '__name__', None)
            if callback_cls == viewset_cls.__name__:
                route = pattern.pattern.regex.pattern
                base_route = re.sub(r'\(\?P<\w+>[^)]+\)', '', route).rstrip('$').rstrip('/')
                prefix = base_route.strip('/').replace('/', ':')
                return prefix
        elif isinstance(pattern, URLResolver):
            # include 안쪽으로 재귀 탐색
            found = find_viewset_url_pattern(pattern.url_patterns, viewset_cls)
            if found:
                return found
    return None

def get_cache_prefix_for_viewset(viewset_cls):
    resolver = get_resolver()
    return find_viewset_url_pattern(resolver.url_patterns, viewset_cls)


def remove_duplicates_from_model ( model_class:Model, field_names:list[str] ) -> int:
        """
        return 은 삭제된 record 수 반환
        모든 필드('정부기관', '구분', '제목', '등록일', '링크')가 중복된 레코드를 찾아 삭제합니다.
        가장 최근에 생성된 레코드만 남기고 나머지는 삭제합니다.
        """
        from django.db.models import Count, F, Max
        from django.db import transaction
        
        # 중복 그룹 찾기
        duplicates = model_class.objects.values(
            *field_names
        ).annotate( 


            count=Count('id'),
            max_id=Max('id')  # 가장 큰 ID (최신 레코드) 저장
        ).filter(count__gt=1)
        
        deleted_count = 0
        
        with transaction.atomic():
            for dup in duplicates:
                # 중복 그룹에서 최신 레코드를 제외한 모든 레코드 삭제
                to_delete = model_class.objects.filter(
                    **{field: dup[field] for field in field_names}
                ).exclude(id=dup['max_id'])
                
                deleted_count += to_delete.count()
                to_delete.delete()
                
        return deleted_count

# JSON 직렬화 가능한 형식으로 변환하는 함수
def json_serializable(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)
    

class CustomDecimalField(serializers.DecimalField):
    def to_internal_value(self, data):
        #### float 값도  DecimalField 로 변환
        if isinstance(data, float):
            try:
                return super().to_internal_value(Decimal(str(data)))
            except Exception as e:
                print ( e )
                self.fail('invalid', value=data)
        return super().to_internal_value(data)

def get_tableName_from_api권한( div:str = '영업수주', name:str = '관리' ) -> int:
    """ div 와 name 을 받아서 해당하는 테이블의 id 를 반환합니다. """
    return User_models.Api_App권한.objects.get(div=div, name=name).id


def generate_table_config_db_from_viewset(MODEL, div:str, name:str, serializer):

    TABLE_NAME = f"{div}_{name}_appID_{get_tableName_from_api권한(div=div, name=name)}"

    if (qs:= Config_Models.Table_Config.objects.filter(table_name=TABLE_NAME) ):
        qs.delete()

    _isSuccess = generate_table_config_db( 
        table_name=TABLE_NAME, 
        model_field = get_MODEL_field_type(MODEL),
        serializer_field = get_Serializer_field_type( serializer ),
    )
    if _isSuccess:
        print ( f'{TABLE_NAME} 테이블 설정 생성 완료' )
    else:
        print ( f'{TABLE_NAME} 테이블 설정 생성 실패' )


def generate_table_config_db( table_instance:Config_Models.Table, serializer_field:dict, **kwargs):
    # serializer_field = kwargs.pop('serializer_field')
    _dict = {}
    success = []
    for _idx, (key, value) in enumerate(serializer_field.items()):
    #    _dict['table_name'] = table_name
        _dict['column_name'] = key
        _dict['display_name'] = key
        _dict['column_type'] =  value #### type(value).__name__
        _dict['order'] = _idx
        _isSuccess =write_table_config_db( table_instance=table_instance, **_dict )
        success.append( _isSuccess )
        
    return all(success)
        # write_table_config_db( table_name=table_name, **{key:value} )

def write_table_config_db( table_instance:Config_Models.Table, **kwargs ) -> bool:
    """ table_name 에 해당하는 테이블의 설정을 생성합니다. """
    try:
        from django.db import transaction
        with transaction.atomic():
            if 'id' in kwargs:
                _instance = Config_Models.Table_Config.objects.get(id=kwargs['id'])
                _instance.save( **kwargs  )

            else:
                Config_Models.Table_Config.objects.create(table=table_instance, **kwargs)
        return True
    except Exception as e:
        print(f"  - 오류: {table_instance.table_name} 처리 중 예외 발생: {e}")
        traceback.print_exc()
        return False

def remove_brackets_and_content(text: str) -> str:
    """
    문자열에서 괄호와 괄호 안의 내용을 모두 삭제합니다.
    
    Args:
        text: 처리할 문자열
    
    Returns:
        str: 괄호와 괄호 안 내용이 제거된 문자열
    
    예시:
        "안녕하세요 (여기는 삭제) 반갑습니다" -> "안녕하세요  반갑습니다"
    """
    import re
    # 소괄호(), 대괄호[], 중괄호{} 모두 처리
    pattern = r'[\(\[\{].*?[\)\]\}]'
    return re.sub(pattern, '', text)

def showinfo(f):
    @wraps(f)
    def wrapper(*args, **kwds):
         print(f.__name__, f.__hash__)
         return f(*args, **kwds)
    return wrapper


def _get_receivers_from_appQS(app_ids:list[int]) -> list[int]:
    """ app_ids 에 해당하는 사용자들의 id 를 반환합니다. """
    app_권한_qs = User_models.Api_App권한.objects.filter(pk__in=app_ids)
    user_ids = app_권한_qs.values_list('user_pks', flat=True).distinct()
    unique_user_ids = list(set(user_id for user_id in user_ids if user_id is not None))
    return unique_user_ids

from websocket import create_connection
def send_WS_msg_short(  _instance:Model, url:str, msg:dict ) -> bool:
    """ kwargs 로 받아서 처리하는 함수 
        _instance : Model instance
        url : str
        msg : dict
        msg type :
            {
                "main_type":('message','alarm','notice', 'error', 'warning','success', 'info'),
                "sub_type":'규약이 필요',
                "receiver": ['ALL'], # ['ALL'], ['USER_ID'], ['USER_ID_LIST']
                "subject":str,
                "message":str ( json ) ==> app마다 규약이 필요
                "sender": fk,                                
                "send_time" :  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                +
                그외는 app 마다 규약 사항
            }
        return : bool   
    """
    try:
        ws = create_connection(url)
        msg["send_time"] =  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        msg['message'] = json.dumps( msg['message'], ensure_ascii=False ) if isinstance( msg['message'], dict ) else msg['message']
        result = ws.send ( json.dumps ( msg, ensure_ascii=False ) )
        if 'file' in msg:
            del msg['file']['content']
        print ( 'ws_send_msg:', msg  )
        ws.close()
        # print ( _instance )
        return True
    except Exception as e:
        print ( 'ws_send_error:', _instance, 'error:', e )
        return False


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper

def generate_Path() -> str:
    path_dir = './media/server-made/download/'
    path_dir +=str(uuid.uuid4()) +'/'
    Path(path_dir).mkdir(parents=True, exist_ok=True)
    return ( path_dir)    


def get_MODEL_field_type(model: Model) ->dict[str:str]:
    """ model을 받아서 { fieldname:fieldtype } 형태로 return """
    db_field = {}
    for field in  [field.name	for field in model._meta.get_fields() ]:
        db_field[field] = model._meta.get_field(field).get_internal_type()
    logger.debug( 'get_MODEL_field_type(model):')
    logger.debug ( db_field)
    return db_field

def get_Serializer_field_type(_serializer: serializers.ModelSerializer) -> dict[str, str]:
    """ModelSerializer에서 {fieldname: fieldtype} 형태로 반환 (SerializerMethodField는 모델 기준으로 fallback)"""
    fields_dict = _serializer.get_fields()
    model_class = getattr(getattr(_serializer, 'Meta', None), 'model', None)

    result = {}

    for name, field in fields_dict.items():
        # 우선 기본 field type
        field_type = type(field).__name__

        # 만약 SerializerMethodField이면 모델에서 찾아보기
        if field_type == 'SerializerMethodField' and model_class:
            try:
                model_field = model_class._meta.get_field(name)
                field_type = type(model_field).__name__
            except (FieldDoesNotExist, AttributeError):
                pass  # 모델에 없는 field면 그대로 둠

        # 예외 처리: TextArea 템플릿
        if isinstance(field, serializers.CharField) and field.style.get("base_template") == "textarea.html":
            field_type = "TextField"

        result[name] = field_type

    logger.debug('get_Serializer_field_type(_serializer):')
    logger.debug(result)
    return result

# def get_Serializer_field_type(_serializer:serializers.ModelSerializer) ->dict[str:str]:
#     """ modelserializer instance 를 방아서 {fieldname:fieldtype} 형태로 return """
#     fields_dict = _serializer.get_fields()
#     result = {}
#     for name, field in fields_dict.items():
#         if isinstance(field, serializers.CharField) and field.style.get("base_template") == "textarea.html":
#             result[name] = "TextField"
#         else:
#             result[name] = type(field).__name__
#     logger.debug( 'get_Serializer_field_type(_serializer):')
#     logger.debug ( result )
#     return result

#     fields_dict = _serializer.get_fields()
#     print ( 'get_Serializer_field_type(_serializer):')
#     print ( fields_dict )
#     return { name:_type for ( name, _type) in fields_dict.items() }


def get_List_deleted( original_list:list, delete_list:list):
    """
    원본 리스트에서 삭제할 리스트의 요소들을 제외한 새로운 리스트를 반환합니다.
    
    Args:
        original_list: 원본 리스트
        delete_list: 제외할 요소들이 담긴 리스트
    
    Returns:
        list: 필터링된 새로운 리스트
    """
    if not delete_list : return original_list
    return [item for item in original_list if item not in delete_list]


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR','')
    return ip