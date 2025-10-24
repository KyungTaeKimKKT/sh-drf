from django.db import models,transaction
from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import receiver
from . import models as Models_DB
# import 생산관리.models
import util.utils_func as Utils

from django.core.cache import cache


# 캐시 키 상수 정의
생산관리_ProductionLine_CACHE_KEY = '생산관리_ProductionLine'
생산관리_생산계획_DDay_CACHE_KEY = '생산관리_생산계획_DDay'


@receiver([post_save, post_delete], sender=Models_DB.ProductionLine )
def clear_생산관리_ProductionLine_cache(sender, instance, **kwargs):
    """모델이 변경되거나 삭제될 때 캐시를 초기화합니다"""
    cache.delete(생산관리_ProductionLine_CACHE_KEY)


@receiver([post_save, post_delete], sender=Models_DB.생산계획_DDay )
def clear_생산계획_DDay_cache(sender, instance, **kwargs):
    """모델이 변경되거나 삭제될 때 캐시를 초기화합니다"""
    cache.delete(생산관리_생산계획_DDay_CACHE_KEY)



def _get_출하_type(적용:str) -> str:
	_dict = {
		'Cage': ['wall', '상판', 'car'],
		'Door': ['hatch'],
		'JAMB': ['jamb']
	}
	
	# 입력 문자열을 소문자로 변환
	input_str = 적용.lower()
	
	# 딕셔너리를 순회하면서 확인
	for key, value_list in _dict.items():
		# value_list의 각 요소를 소문자로 변환하여 비교
		for value in value_list:
			if input_str.find(value.lower()) != -1:
				return key
	
	# 일치하는 것이 없을 경우 None 반환
	return None

# Signal 처리를 위한 receiver 함수
@receiver(post_save, sender=Models_DB.생산계획_일정관리)
def handle_일정관리_changed(sender, instance:Models_DB.생산계획_일정관리, **kwargs):
	print ( sender , ': post-save :',  instance)



@receiver(post_save, sender=Models_DB.Schedule_By_Types)
def handle_Schedule_change(sender:Models_DB.Schedule_By_Types, instance:Models_DB.Schedule_By_Types, **kwargs):
	URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/production_schedule/"
	# 이전 기록 가져오기
	try:
		previous_record = instance.history.filter(
			history_date__lt=instance.history.latest().history_date
		).latest()
		# False에서 True로 변경된 경우에만 처리
		if instance.출하일 and previous_record.출하일 != instance.출하일:
			msg = {
				"type":"broadcast",
				"sender":"system",
				"id" : instance.id, 
				"message" : "changed"
				# "message": f"\n고객사: {instance.고객사} ,\n제목:{instance.Job_Name} ,\n 차수: {str(instance.차수)} , \n Rev. {str(instance.Rev)} \n배포되었읍니다.!!!\n\n",            
			}
			Utils.send_WS_msg_short( instance, url= URL_WS, msg=msg)

			#### 😀Models_DB.생산계획_확정Branch get_or_create 
			# 일정관리_obj = Models_DB.생산계획_일정관리.objects.get(schedule_fks__id = instance.id ) 
			일정관리_obj = Models_DB.생산계획_일정관리.objects.filter(
					models.Q(schedule_cage_fk=instance) |
					models.Q(schedule_door_fk=instance) |
					models.Q(schedule_jamb_fk=instance)
				).last()

			생산지시_obj = 일정관리_obj.생산지시_fk
			print ( 'models.Schedule_By_Types: ', instance)
			for process in 생산지시_obj.process_fks.all(): 
				print ( _get_출하_type(process.적용), instance.출하_type)
				if _get_출하_type(process.적용) == instance.출하_type:
					_inst, _created = Models_DB.생산계획_확정Branch.objects.get_or_create( 
						일정관리_fk = 일정관리_obj, 
						schedule_fk=instance, 
						생산지시_process_fk=process,
						# 계획수량 = process.수량
								)




	except instance.history.model.DoesNotExist:
		print ( 'error:', 'handle_status_change' )
		pass