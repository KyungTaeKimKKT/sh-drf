from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.conf import settings
from django.dispatch import receiver
from django.core.cache import cache
from collections import OrderedDict
from . import models as User_models
import json
from decimal import Decimal
from config.models import WS_URLS_DB
# 캐시 키 상수 정의
USER_LIST_CACHE_KEY = 'user_list_관리'
USER_VIEW_CACHE_KEY = 'user_list_view'
APP_DEV_CACHE_KEY = 'App_list_개발자'
APP_ADMIN_CACHE_KEY = 'App_list_admin'

import util.utils_func as Utils
from util.redis_publisher import RedisPublisher

import logging, traceback
logger = logging.getLogger('config')

@receiver(post_save, sender=User_models.ErrorLog)
def ErrorLog_save(sender, instance, **kwargs):
    """ error log 저장시 웹소켓 전송 """
    return 
    from users.serializers import ErrorLogSerializer
    serializer = ErrorLogSerializer(instance)
    _receiverObj = User_models.Api_App권한.objects.get( pk = 188).user_pks.all()
    _receiver = [ obj.id for obj in _receiverObj ]

    # Decimal 객체를 float로 변환하는 사용자 정의 JSON 인코더
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return super(DecimalEncoder, self).default(obj)
    msg = {
        "main_type":"notice",
        "sub_type": "ErrorLog_저장",
        "receiver": _receiver,
        "subject":"ErrorLog_저장",
        "message": json.dumps(dict(serializer.data), cls=DecimalEncoder) , ### item은 OrderedDict
        "sender": 1,
    }
    print ( msg )
    Utils.send_WS_msg_short( instance, url= settings.WS_ERROR_LOG_CREATED, msg=msg)

@receiver([post_save, post_delete], sender=User_models.User)
def clear_user_list_cache(sender, instance, **kwargs):
    """User 모델이 변경되거나 삭제될 때 캐시를 초기화합니다"""
    cache.delete(USER_LIST_CACHE_KEY)
    cache.delete(USER_VIEW_CACHE_KEY)


@receiver(post_save, sender=User_models.Api_App권한)
@receiver(post_delete, sender=User_models.Api_App권한)
def Api_App권한_changed(sender, instance:User_models.Api_App권한,  **kwargs):
    """ Api_App권한 변경시 웹소켓 전송 """
    return 
    handle_name = 'app_권한'
    cache.delete(APP_DEV_CACHE_KEY)
    cache.delete(APP_ADMIN_CACHE_KEY)
    # qs = User_models.Api_App권한.objects.order_by('순서','div','name').prefetch_related('user_pks')
    from users.serializers import Api_App권한Serializer
    try:
        logger.info(f" Api_App권한_changed : instance : {instance} , kwargs : {kwargs} ")
        ws_handle_obj = WS_URLS_DB.objects.get(name=handle_name)
        ### 변경만 전송
        if instance.pk:
            serializer = Api_App권한Serializer(instance)
            table_name = f"{instance.div}_{instance.name}_appID_{instance.id}"
            if 'created' in kwargs:
                created = kwargs['created']
                if created:
                    with transaction.atomic():
                        ### 테이블 생성
                        from config.models import Table
                        table_instance = Table.objects.create(
                            table_name = table_name,
                        )
                        ### admin 사용자 추가
                        from users.models import Api_App권한_User_M2M
                        Api_App권한_User_M2M.objects.create(
                            app_권한 = instance,
                            user_id = 1,
                        )           
                        #### 테이블 설정 생성
                        #### table config 생성
                        if instance.TO_MODEL and instance.TO_Serializer:
                            from util.generate_tableconfig_from_app_auth import generate_table_configs_from_app_auth, get_model_and_serializer
                            # 모델과 시리얼라이저 가져오기
                            model_class, serializer_instance = get_model_and_serializer(
                                instance.TO_MODEL, 
                                instance.TO_Serializer
                            )
                            with transaction.atomic():
                                 Utils.generate_table_config_db(
                                        table_instance=table_instance,
                                        model_field = Utils.get_MODEL_field_type(model_class),
                                        serializer_field = Utils.get_Serializer_field_type( serializer_instance ),
                                    )


                        #### table menu 생성
                        with transaction.atomic():
                            from config.models import TableVHeaderLink, TableHHeaderLink, TableCellMenuLink
                            from config.models import H_Header_Menus, V_Header_Menus, Cell_Menus
                            for index, menu in enumerate(H_Header_Menus.objects.all()):
                                TableHHeaderLink.objects.create(
                                    table=table_instance,
                                    h_header = menu,
                                    order = index
                                )
                            for index, menu in enumerate(V_Header_Menus.objects.all()):
                                TableVHeaderLink.objects.create(
                                    table=table_instance,
                                    v_header = menu,
                                    order = index
                                )
                            for index, menu in enumerate(Cell_Menus.objects.all()):
                                TableCellMenuLink.objects.create(
                                    table=table_instance,
                                    cell_menu = menu,
                                    order = index
                                )

                else:
                    logger.info(f" Api_App권한_changed : updated되었습니다.")
            else:
                logger.info(f" Api_App권한_changed : deleted되었습니다.")
                try:
                    with transaction.atomic():
                        from config.models import Table
                        table_instance = Table.objects.get(table_name=table_name)
                        table_instance.delete()
                except Exception as e:
                    logger.error(f" Api_App권한_changed : Table 삭제 실패: {e}")
                    logger.error(traceback.format_exc())

        ###  cache delete
        # cache.delete(f"broadcast:app_authority_init")
        trigger_channel = f"{ws_handle_obj.group}:{ws_handle_obj.channel}_init"
        publisher = RedisPublisher()
        redis_msg = {
            "main_type": ws_handle_obj.group,
            "sub_type": ws_handle_obj.name,
            "action": 'init',
            "receiver" : ['All'],
            "message": serializer.data
        }
        구독자수 = publisher.publish(
                channel= trigger_channel, 
                message= redis_msg ,
            )
        logger.info(f" Api_App권한_changed : Redis 발행 완료: 구독자수 {구독자수}")

    except Exception as e:
        logger.error(f" Api_App권한_changed : Error sending WS message: {e}")
        logger.error(traceback.format_exc())