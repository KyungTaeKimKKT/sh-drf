from django.db import models,transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from . import models as mbo_models
from users.models import Api_App권한

import util.utils_func as Utils

@receiver(post_save, sender=mbo_models.영업mbo_설정DB)
@receiver(post_delete, sender=mbo_models.영업mbo_설정DB)
def handle_status_change(sender:mbo_models.영업mbo_설정DB, instance:mbo_models.영업mbo_설정DB, **kwargs):

	URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/work_order/"
	# 이전 기록 가져오기
	try:
		if instance.is_시작:
			if not instance.is_완료:
				for id in [ 157,158 ] : ## 사용자등록, 관리자등록
					obj = Api_App권한.objects.get(id = id)
					if not obj.is_Run : 
						obj.is_Run = True
						obj.save()
			else:
				for id in [ 157,158 ] : ## 사용자등록, 관리자등록
					obj = Api_App권한.objects.get(id = id)
					if obj.is_Run : 
						obj.is_Run = False
						obj.save()
		else:
			for id in [ 157,158 ] : ## 사용자등록, 관리자등록
				obj = Api_App권한.objects.get(id = id)
				if obj.is_Run : 
					obj.is_Run = False
					obj.save()

			## 

	except Exception as e:
		# 첫 번째 생성인 경우
		print ( 'signals.py error:', 'handle_status_change', e )
		