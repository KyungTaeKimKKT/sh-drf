from __future__ import annotations
from typing import cast
from django_redis.cache import RedisCache
from django_redis.client import DefaultClient
from django.core.cache import cache as _cache

cache = cast(RedisCache, _cache)
client = cast(DefaultClient, cache.client.get_client())


# from django.core.cache import cache
# from django_redis.cache import RedisCache
# cache: RedisCache
import time, json
from collections import defaultdict
from urllib.parse import unquote
from users.models import Api_App권한
DEFAULT_CACHE_TIMEOUT = 60*5


def cache_delete_pattern(pattern: str):
    client = cache.client.get_client()
    cursor = "0"
    total = 0

    while True:
        cursor, keys = client.scan(cursor=cursor, match=pattern, count=1000)
        if keys:
            client.unlink(*keys)
            total += len(keys)
        if cursor == "0":
            break

    print(f"cache_delete_pattern: {pattern}  삭제 {total}건")

def clear_all_cache_by_handle(handle:str):
    """ handle은 config.models.WS_URLS_DB 의 name 필드 값으로 지정해야 함. """
    try:
        from config.models import WS_URLS_DB
        ws_handle_obj = WS_URLS_DB.objects.get(name=handle)
        trigger_channel = f"{ws_handle_obj.group}:{ws_handle_obj.channel}"
        clear_all_cache(base=trigger_channel)
    except Exception as e:
        print(f"clear_all_cache_by_handle 오류: {e}")

####  캐시 all clear
def clear_all_cache(base:str=None):
    if base:
        del_pattern = f'{base}:*'.replace("::", ":")
        print(f"clear_all_cache: {base}    {del_pattern}")
        cache_delete_pattern(del_pattern)
    else:
        cache.clear()

def clear_cache(key:str):
    cache.delete(key)

#### 캐시 관리 함수
def set_cache(key:str, value:any, timeout:int=DEFAULT_CACHE_TIMEOUT):
    """
    json 형태로 저장
    """
    if not isinstance(timeout, int) :
        timeout = DEFAULT_CACHE_TIMEOUT
    json_value = json.dumps(value, ensure_ascii=False)

    cache.set(key, json_value, timeout)

def get_cache(key):    
    """
        json 형태로 반환
    """
    value = cache.get(key)  
    try:
        if value:
            return json.loads(value)
        else:
            return None
    except Exception as e:
        print(f"get_cache 오류: {e}")
        return None
    
def get_cache_key(url:str, *args):
    """
    주어진 URL 문자열을 Redis에 사용할 수 있는 캐시 키 형식으로 변환합니다.
    - URI 인코딩된 문자열을 디코딩 (예: %EC%98%81 → 영)
    - 슬래시('/')는 Redis key 네임스페이스를 위한 콜론(':')으로 변환
    - 끝에 붙은 콜론은 제거

    예시:
        /영업mbo/설정DB/get-매출년도list/ → 영업mbo:설정DB:get-매출년도list

    Args:
        url (str): request.get_full_path() 결과값
        *args: 확장 가능성을 위한 여유 인자

    Returns:
        str: Redis 캐시 키로 사용할 문자열
    """
    return unquote(url).replace('/', ':').strip(':')

### 
def clear_사용자별_app권한_캐시(key:str = '사용자별_app권한_캐시'):
    cache.delete_pattern(f"{key}:*")

def set_사용자별_app권한_캐시(key:str = '사용자별_app권한_캐시'):
    """
    app권한 별 사용자 캐쉬
    { app_id : [user_pk1, user_pk2, ...] }
    """
    try:
        from users.models import Api_App권한, Api_App권한_User_M2M
        start_time = time.time()
        cache_data = defaultdict(list)
        qs = Api_App권한_User_M2M.objects.select_related('app_권한').values_list('app_권한_id', 'user_id')
        for app_id, user_id in qs:
            key_full = f"{key}:{app_id}"
            cache_data[key_full].append(user_id)
        
        for key_full, value in cache_data.items():
            set_cache(key_full, value, timeout=10*1)

        end_time = time.time()
        print(f"캐시 셋팅 시간: {int((end_time - start_time) * 1000)} msec")
    except Exception as e:
        print(f"set_사용자별_app권한_캐시 오류: {e}")

def get_사용자별_app권한_캐시(key:str = '사용자별_app권한_캐시', app_instance:Api_App권한=None):
    """
    """
    if app_instance is None:
        return None
    key_full = f"{key}:{app_instance.id}"
    return get_cache(key_full)    

def delete_사용자별_app권한_캐시(key:str = '사용자별_app권한_캐시', app_id:int =  -1):
    """
    """
    if app_id == -1:
        return 
    key_full = f"{key}:{app_id}"
    cache.delete(key_full)


#### mbo 매출녇도
def set_mbo_매출년도_캐시(key:str = '영업MBO:매출년도_캐시'):
    """
    """
    try:
        key = get_cache_key(key)
        from 영업mbo.models import 영업mbo_설정DB
        _list = list(
					영업mbo_설정DB.objects.order_by('-매출_year')
					.values_list('매출_year', flat=True)
					.distinct()
				)
        print(f"set_mbo_매출년도_캐시: {_list}")
        set_cache(key, _list, timeout=60)
    except Exception as e:
        print(f"set_mbo_매출년도_캐시 오류: {e}")

def get_mbo_매출년도_캐시(key:str = '영업MBO:매출년도_캐시'):
    """
    """
    try:
        key = get_cache_key(key)
        value = get_cache(key)
        if value:
            return value
        else:
            set_mbo_매출년도_캐시(key)
            return get_cache(key)
    except Exception as e:
        print(f"get_mbo_매출년도_캐시 오류: {e}")
        return None
    
def get_ws_url_db_all( key:str = 'WS_URLS_DB')->str:
    """
    cache는 serializer.data 형태로 저장되어 있음.
    """
    data = cache.get(key)
    print(f"get_ws_url_db_all: {bool(data)}")
    if data :
        return data
    else :
        return set_ws_url_db_all(key)

def set_ws_url_db_all(key:str = 'WS_URLS_DB', timeout:int = 60*60*1) ->str:
    """
    """
    from config.models import WS_URLS_DB
    from config.serializers import WS_URLS_DB_Serializer
    qs = WS_URLS_DB.objects.filter(is_active=True)
    data = WS_URLS_DB_Serializer(qs, many=True).data
    cache.set(key,data, timeout=timeout)
    return data

def clear_ws_url_db_all(key:str = 'WS_URLS_DB'):
    print(f"clear_ws_url_db_all: {key}")
    cache.delete_pattern(f"{key}*")