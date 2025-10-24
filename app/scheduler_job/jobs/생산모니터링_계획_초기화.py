from  django.db import transaction
import time
from datetime import date, timedelta, datetime
import 생산모니터링.models_외부 as Models_외부 
import 생산모니터링.models as Models_내부

import logging, traceback
logger = logging.getLogger(__name__)

def main_job(job_id:int):
	s = time.time()

	yesterday = date.today() - timedelta(days=1)
	today = date.today()
	try:
		생산계획_qs = Models_외부.생산계획실적.objects.using('생산모니터링').\
							filter(start_time__contains=yesterday).order_by('sensor_id')
		
		# 데이터가 없는 경우 먼저 확인
		if not 생산계획_qs.exists():
			logger.error("어제 생산계획 데이터가 존재하지 않습니다.")
			return {
				'log': "어제 생산계획 데이터가 존재하지 않습니다.",
				'redis_publish': None
			}
		
		# 필요한 필드만 업데이트하는 함수
		def 필드_추출(계획 : Models_외부.생산계획실적):

			update_fields = ['id','start_time', 'end_time', 'job_qty', '등록자'] ## id는 삭제됨
			# 어제 데이터를 복사하되 4개 필드만 업데이트
			새_계획 = {}
			for field in 계획._meta.fields:
				if field.name not in update_fields:
					새_계획[field.name] = getattr(계획, field.name)
			
			# 4개 필드만 업데이트 (id는 삭제됨)
			새_계획['start_time'] = datetime.combine(today, 계획.start_time.time())
			새_계획['end_time'] = datetime.combine(today, 계획.end_time.time())
			새_계획['job_qty'] = 0
			새_계획['등록자'] = 'admin'
			새_계획['job_qty_time'] = 새_계획['start_time']
			
			return 새_계획
		
		with transaction.atomic():
			# 오늘 데이터 삭제
			삭제_건수 = Models_외부.생산계획실적.objects.using('생산모니터링').filter(start_time__contains=today).delete()[0]
			logger.info(f"{삭제_건수}건의 기존 데이터 삭제됨")
			
			# 새 데이터 생성
			새_계획_목록 = [Models_외부.생산계획실적(**필드_추출(계획)) for 계획 in 생산계획_qs]
			생성된_객체 = Models_외부.생산계획실적.objects.using('생산모니터링').bulk_create(새_계획_목록)
			
		return {
			'log': f"{len(생성된_객체)} 건 초기화 완료 : 소요시간 : {int((time.time() - s) * 1000)} msec",
			'redis_publish': None
		}
	except Exception as e:
		logger.error(f"생산계획실적 초기화 실패 : {e}")
		logger.error(traceback.format_exc())
		return {
			'log': f"생산계획실적 초기화 실패 : {e}",
			'redis_publish': None
		}

