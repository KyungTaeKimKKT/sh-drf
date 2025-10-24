from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models

import util.utils_func as Utils

@receiver(post_save, sender=models.작업지침)
def handle_status_change(sender:models.작업지침, instance:models.작업지침, **kwargs):
    URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/work_instruction/"
    # 이전 기록 가져오기
    try:
        previous_record = instance.history.filter(
            history_date__lt=instance.history.latest().history_date
        ).latest()
        # False에서 True로 변경된 경우에만 처리
        if not previous_record.is_배포 and instance.is_배포:
            msg = {
            "type":"broadcast",
            "sender":"system",
            "id" : instance.id, 
            "message": f"\n고객사: {instance.고객사} ,\n제목:{instance.제목} ,\n Rev. {str(instance.Rev)} \n배포되었읍니다.!!!\n\n",            
            }
            Utils.send_WS_msg_short( instance, url= URL_WS, msg=msg)
    except instance.history.model.DoesNotExist:
        # 첫 번째 생성인 경우
        print ( 'error:', 'handle_status_change' )
        pass