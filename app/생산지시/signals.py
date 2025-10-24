from django.db import models,transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models
import 생산관리.models
import util.utils_func as Utils

@receiver(post_save, sender=models.생산지시)
def handle_status_change(sender:models.생산지시, instance:models.생산지시, **kwargs):
	URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/work_order/"
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
			"message": f"\n고객사: {instance.고객사} ,\n제목:{instance.Job_Name} ,\n 차수: {str(instance.차수)} , \n Rev. {str(instance.Rev)} \n배포되었읍니다.!!!\n\n",            
			}
			Utils.send_WS_msg_short( instance, url= URL_WS, msg=msg)

			# with transaction.atomic():
			# 	dday = 생산관리.models.생산계획_DDay.objects.first()  # 기본 DDay 설정 가져오기
			# 	if not 생산관리.models.생산계획_일정관리.objects.filter(생산지시_fk=instance).exists():
			# 		생산관리.models.생산계획_일정관리.create_schedules(instance)
			
			생산관리.models.생산계획_일정관리.objects.create(생산지시_fk = instance )
			## 

	except instance.history.model.DoesNotExist:
		# 첫 번째 생성인 경우
		print ( 'error:', 'handle_status_change' )
		pass