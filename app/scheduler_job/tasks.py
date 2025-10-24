from celery import shared_task
import logging,  copy, time
from datetime import date, datetime, timedelta
from django.core.cache import cache
from django.db import close_old_connections
import importlib
import os, traceback
import threading
from .models import Scheduler_Job, Scheduler_Job_Status, Scheduler_Job_Log

logger = logging.getLogger('scheduler_job')
from util.redis_publisher import RedisPublisher


def get_redis_msg(data:list[dict], job:Scheduler_Job=None):
    redis_msg = {
        "main_type": 'celery-notice',
        "sub_type": 'broadcast',
        "subject": job.job_info.name,
        "action": 'update',
        "receiver" : 'All',
        "message": data,
        "timestamp": datetime.now().isoformat()
    }
    return redis_msg

def publish_redis(data:list[dict], channel:str='broadcast/celery', job:Scheduler_Job=None) -> int:

    publisher = RedisPublisher()
    # logger.info(f"publish_redis 호출됨: publisher={publisher}")
    redis_msg = get_redis_msg(data, job)
    구독자수 = publisher.publish(
        channel= channel, 
        message= redis_msg ,
    )
    return 구독자수

# @shared_task
def task_test():
    """
    기존 APScheduler에서 실행하던 작업을 Celery 태스크로 변환
    """
    logger.info("주기적 작업 실행 중...")  # print 대신 logger.info 사용
    print("이 메시지는 표준 출력으로 전송됩니다")  # 테스트용으로 남겨둠
    # 여기에 기존 작업 로직 구현
    return "작업 완료"

@shared_task(bind=True)
def execute_scheduled_job(self, job_id):
    """스케줄러 작업을 실행하는 Celery 태스크"""
    ####  25-8-18 close_old_connections() 추가
    close_old_connections()

    job = Scheduler_Job.objects.get(id=job_id)
    
    # 작업 상태 기록 생성   
    if job.is_db_status:
        job_status = Scheduler_Job_Status.objects.create(
            job=job,
            pid=os.getpid(),
            thread_id=threading.current_thread().name
        )
    
    start_time = time.time()
    success = False
    log_data = {}
    redis_pub_data = None
    
    try:
        # job_info에서 함수 경로 가져오기
        function_path = job.job_info.job_function
        module_path, function_name = function_path.rsplit('.', 1)
        
        # 동적으로 함수 임포트
        module = importlib.import_module(module_path)
        function = getattr(module, function_name)
        
        # 함수 실행
        result = function(job_id)
        # logger.info(f"result: {result}")
        log_data = result.get('log', {'message': '로그 정보 없음'}  )
        redis_pub_data = result.get('redis_publish', None)
        
        success = True
        # log_data = {"result": result, "message": "작업이 성공적으로 완료되었습니다."}
        
    except Exception as e:
        log_data = {"error": str(e), "message": "작업 실행 중 오류가 발생했습니다."}
    finally:
        # 작업 완료 시간 계산
        end_time = time.time()
        execution_time_ms = int((end_time - start_time) * 1000)
        
        # 작업 상태 업데이트
        if job.is_db_status:
            job_status.end_time = datetime.now().isoformat()
            job_status.status = 'completed' if success else 'failed'
            job_status.save()
        
        # 작업 로그 저장
        if job.is_db_log:
            Scheduler_Job_Log.objects.create(
                job=job,
                success=success,
                log=log_data,
                execution_time_ms=execution_time_ms
            )
        
        ### redis 발행 broadcast/celery => broadcast:celery로 변환
        try:
            if  (channel_name := job.job_info.redis_channel ):
                if channel_name and len(channel_name) > 5 and redis_pub_data:
                    구독자수=publish_redis(redis_pub_data, channel_name, job=job)
                    logger.info(f"구독자수: {구독자수}, 채널: {channel_name}")
            else:
                logger.error (f"Redis 발행 오류 :channel_name 없음 : {job.job_info.name}")
        except Exception as e:
            logger.error(f"redis 발행 오류: {e}")
        finally:
            #### 25-8-18 close_old_connections() 추가
            close_old_connections()
            
        return log_data
