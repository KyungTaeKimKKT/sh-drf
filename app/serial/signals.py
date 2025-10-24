from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

from . import models as SerialModels

import util.utils_func as Utils

@receiver(post_save, sender = SerialModels.SerialHistory )
def handle_SerialHistory_Create (sender:SerialModels.SerialHistory, instance:SerialModels.SerialHistory , created:bool, **kwargs):
    if not created : return 

    URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/serial-scan-complete/"
    # 이전 기록 가져오기
    try:
        msg = 'SerialHistory Create'
        Utils.send_WS_msg_short( instance, url= URL_WS, msg=msg)

        cache_key = f'실적수량_{instance.serial_fk.확정Branch_fk.id}_{instance.ProductionLine_fk.id}'
        cache.delete(cache_key)

    except Exception as e:
        print ( 'error:', e )
