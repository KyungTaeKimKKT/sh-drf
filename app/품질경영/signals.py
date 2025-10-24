from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.dispatch import receiver
from django.core.cache import cache
from collections import OrderedDict
from . import models as 품질경영_models
from users.models import Api_App권한
import json
# 캐시 키 상수 정의
# USER_LIST_CACHE_KEY = 'user_list_관리'
# USER_VIEW_CACHE_KEY = 'user_list_view'
# APP_DEV_CACHE_KEY = 'App_list_개발자'
# APP_ADMIN_CACHE_KEY = 'App_list_admin'

import util.utils_func as Utils




@receiver(post_save, sender=품질경영_models.CS_Claim )
@receiver(post_delete, sender=품질경영_models.CS_Claim )
def CS_Claim_changed(sender, instance:품질경영_models.CS_Claim, **kwargs):
    return 
    # cache.delete(APP_DEV_CACHE_KEY)
    # cache.delete(APP_ADMIN_CACHE_KEY)
    # qs = User_models.Api_App권한.objects.order_by('순서','div','name').prefetch_related('user_pks')
    from . import serializers
    serializer = serializers.CS_Claim_Serializer(instance)
    app_권한_qs = Api_App권한.objects.filter(pk__in=[135,137,138,187])
    
    # M2M Field인 user_pks 값들의 values_list의 unique 한 list 구하기
    user_ids = app_권한_qs.values_list('user_pks', flat=True).distinct()
    unique_user_ids = list(set(user_id for user_id in user_ids if user_id is not None))

    print ( instance)
    if instance.진행현황 != '작성':

        msg = {
            "main_type":"notice",
            "sub_type": "CS_Claim_DB_변경",
            "receiver": unique_user_ids,
            "subject":"CS_Claim_DB_변경",
            "app_ids" : [135,137,138,187],
            "message": dict(serializer.data) , ### item은 OrderedDict
            "sender": 1,
        }
        print ( msg )
        Utils.send_WS_msg_short( instance, url= settings.WS_CS_CLAIM_CHANGED, msg=msg)