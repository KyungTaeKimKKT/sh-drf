from __future__ import absolute_import, unicode_literals

from django.core.cache import cache
from config.models import WS_URLS_DB
from util.redis_publisher import RedisPublisher
import util.cache_manager as Cache_Manager
import logging
logger = logging.getLogger(__name__)

def trigger_ws_redis_pub( handle_name:str='table_total_config'):
    """ 
    WS REDIS PUB 트리거 
    handle_name : 트리거 할 핸들명 으로, config/models.py 에 있는 WS_URLS_DB 의 name 필드 값으로 지정해야 함.
    'table_total_config' , 
    """
    try:
        list_handle_name = ['table_total_config', 'app_권한', 'active_users', 'gongji']

        ws_handle_obj = WS_URLS_DB.objects.get(name=handle_name)
        
        base_channel = f"{ws_handle_obj.group}:{ws_handle_obj.channel}"
        trigger_channel = f"{base_channel}:init_trigger"
        Cache_Manager.clear_all_cache(base=base_channel)
        publisher = RedisPublisher()
        redis_msg = {
            "main_type": "init",
            "sub_type": "response",
            "action": 'init',
            "subject": ws_handle_obj.name,
            "receiver" : 'All',
            "message": {}
        }
        구독자수 = publisher.publish(
                channel= trigger_channel, 
                message= redis_msg ,
            )
        return True
    
    except Exception as e:
        logger.error( f"bulk_update 실패 : {trigger_channel} , 구독자수 : {구독자수}")
        return False
