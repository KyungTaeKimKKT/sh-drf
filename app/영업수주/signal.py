from django.db.models.signals import post_save
from django.dispatch import receiver

import shapi.settings as Settings
from . import models as 영업수주Models

def process_자재내역_To_의장_Mapping() -> list[dict]:
    MODEL = 영업수주Models.영업수주_금액
    values = list(MODEL.objects.values('자재내역').distinct())
    values.sort(key=lambda x: x['자재내역'])
    result = []
    # 각 고유한 자재내역에 대해 자재내역_fk 값을 함께 반환합니다
    for item in values:
        if item['자재내역']:
            # 해당 자재내역의 첫 번째 레코드에서 자재내역_fk 값을 가져옵니다
            record = MODEL.objects.filter(자재내역=item['자재내역']).first()
            
            result.append({
                '자재내역': item['자재내역'],
                '의장_fk': record.의장_fk.id if record.의장_fk else None,
                '의장': record.의장_fk.의장 if record.의장_fk  else None
            })
    return result

@receiver(post_save, sender=영업수주Models.자재내역_To_의장_Mapping)
def update_영업수주_금액_의장(sender, instance:영업수주Models.자재내역_To_의장_Mapping, created, **kwargs):
    # 자재내역이 일치하는 영업수주_금액 레코드 찾기
    if not created:
        return 
    QS = 영업수주Models.영업수주_금액.objects.filter(      
        의장_fk__isnull=True
    ).order_by('자재내역')

    ids_to_update = []
    if instance.자재내역:
        keyword_set = set( map(str.strip, instance.자재내역.split(',')))

        for _i, _obj in enumerate(QS):
 
            if all([ keyword.upper() in _obj.자재내역.upper() for keyword in keyword_set ]):
                ids_to_update.append(_obj.id)
    print ( 'ids_to_update: ', ids_to_update )
    # 수집된 ID 목록을 사용하여 bulk 업데이트 수행
    if ids_to_update:
        updated_count = QS.filter(id__in=ids_to_update).update(의장_fk=instance)
        print(f"업데이트된 레코드 수: {updated_count}")
   

    # 웹소켓 통신
    import util.utils_func as Utils
    app_ids = [192]
    unique_user_ids= Utils._get_receivers_from_appQS(app_ids)

    # from . import serializers
    # serializer = serializers.영업수주_금액_Serializer(instance)
    print ( 'ws send:',' 영업수주_금액_의장' )
    Utils.send_WS_msg_short(
        _instance=instance,
        url=Settings.WS_영업수주_금액_DB_UPDATED,

        msg = {
            "main_type":"notice",
            "sub_type": "영업수주_금액_DB_변경_자재내역_의장_변경",
            "receiver": unique_user_ids,
            "subject":"영업수주_금액_DB_에서 자재내역에 대한 의장 변경",
            "app_ids" : app_ids,
            "message": process_자재내역_To_의장_Mapping() , ### item은 OrderedDict
            "sender": 1,
        }
    )