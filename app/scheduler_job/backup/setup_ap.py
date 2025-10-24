# scheduler_job/apscheduler.py
### APScheduler 설정
### DB에서 읽어와서 스케줄러에 등록
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.utils.module_loading import import_string
from django_apscheduler.models import DjangoJobExecution
from apscheduler.triggers.interval import IntervalTrigger
from scheduler_job.job_manager import check_hanging_jobs
# from scheduler_job.job_wrapper import job_wrapper_complete
import sys
import logging
# from scheduler_job.job_wrapper_class import JobWrapper

import logging
import functools
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from scheduler_job.job_manager import register_running_job, unregister_running_job
import sys
import inspect
import util.utils_func as utils_func
import json

# 로거 설정
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# APScheduler 로거 설정
apscheduler_logger = logging.getLogger('apscheduler')
apscheduler_logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 추가
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
scheduler = None

def execute_job(job_function_str, job_id, timeout_seconds=30, *args, **kwargs):
    """
    스케줄러에서 직접 호출할 수 있는 함수
    job_function_str에 지정된 함수를 가져와 job_wrapper_complete로 래핑하여 실행
    """
    from django.utils.module_loading import import_string
    
    try:
        # 함수 문자열로부터 실제 함수 가져오기
        job_function = import_string(job_function_str)
        logger.debug(f"작업 함수 가져옴: {job_function.__name__}, job_id: {job_id}")
        
        # job_wrapper_complete로 래핑하여 실행
        wrapped_function = job_wrapper_complete(job_function, job_id, timeout_seconds)

        
        # 원본 함수에 필요한 모든 인자 전달
        if 'job_id' in inspect.signature(job_function).parameters:
            # job_id를 필요로 하는 함수인 경우
            result = wrapped_function(job_id, *args, **kwargs)
        else:
            # job_id를 필요로 하지 않는 함수인 경우
            result = wrapped_function(*args, **kwargs)
        
        return result
    except Exception as e:
        logger.error(f"작업 실행 중 오류: {e}")
        logger.error(traceback.format_exc())
        raise


def _create_redis_message(redis_pub_message):
    """
    redis_pub_message를 표준 형식으로 변환하여 Serializer 형식으로 변환
    """
    msg = {
        "main_type": "생산모니터링",
        "sub_type": "생산계획실적",
        "action": " broadcast",
        "message": redis_pub_message
    }
    return json.dumps(msg, default=utils_func.json_serializable)


def job_wrapper_complete(func, job_id, timeout_seconds=30):
    """
    작업 함수를 래핑하여 다음 기능을 제공:
    1. 타임아웃 처리
    2. 실행 시간 측정
    3. 작업 상태 관리
    4. 결과 로깅
    5. Redis 발행 (정상 완료 시에만)
    """
    # ensure_logger_has_handlers()
    logger.debug(f"[Wrapper] job_wrapper_complete 정의됨: func={func.__name__}, job_id={job_id}")
    
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        # job_redis_channel을 kwargs에서 추출하고 나머지 kwargs만 원래 함수에 전달
        job_redis_channel = kwargs.pop('job_redis_channel', None)
        logger.debug(f"wrapped_func 호출됨: job_redis_channel={job_redis_channel}")
        print(f"[WRAPPER] wrapped_func 호출됨: job_redis_channel={job_redis_channel}")
        from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log
        from scheduler_job.job_manager import register_running_job, unregister_running_job
        from util.redis_publisher import RedisPublisher  # Redis 발행 클래스 가져오기
        import traceback
        
        # 로그 출력 (표준 출력으로도 출력)
        logger.debug(f"wrapped_func 호출됨: args={args}, kwargs={kwargs}")
        print(f"[WRAPPER] wrapped_func 호출됨: args={args}, kwargs={kwargs}")
        
        logger.debug(f"원래 함수: {func.__name__}, 작업 ID: {job_id}")
        print(f"[WRAPPER] 원래 함수: {func.__name__}, 작업 ID: {job_id}")
        
        # kwargs에서 job_id 확인
        passed_job_id = kwargs.get('job_id')
        logger.debug(f"전달된 job_id: {passed_job_id}, 래퍼에 저장된 job_id: {job_id}")
        print(f"[WRAPPER] 전달된 job_id: {passed_job_id}, 래퍼에 저장된 job_id: {job_id}")
        
        # 실제 사용할 job_id 결정
        actual_job_id = passed_job_id if passed_job_id is not None else job_id
        
        try:
            # 작업 시작 등록
            logger.debug(f"작업 시작 등록 시도: job_id={actual_job_id}")
            print(f"[WRAPPER] 작업 시작 등록 시도: job_id={actual_job_id}")
            
            status_record = register_running_job(actual_job_id)
            logger.debug(f"작업 상태 등록됨: {status_record.id}")
            print(f"[WRAPPER] 작업 상태 등록됨: {status_record.id}")
            
            # 실행 시간 측정 시작
            start_time = time.time()
            
            # 타임아웃 처리
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                  
                    result = future.result(timeout=timeout_seconds)
                    # 기본값 설정
                    log_message = {'default': "작업이 성공적으로 완료되었습니다."}
                    redis_pub_message = None

                    if isinstance(result, dict) and 'log' in result and 'redis_publish' in result:
                        log_message = result['log']
                        redis_pub_message = result['redis_publish']

                    # 실행 시간 계산
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                   
                    unregister_running_job(actual_job_id, status='completed')
                    
                    log_entry = Scheduler_Job_Log.objects.create(
                        job_id=actual_job_id,
                        success=True,
                        log=log_message,
                        execution_time_ms=execution_time_ms
                    )

                    # Redis 발행 (정상 완료 시에만)
                    logger.debug(f"Redis 발행 시도: job_redis_channel={job_redis_channel}, redis_pub_message={redis_pub_message}")
                    print(f"[WRAPPER] Redis 발행 시도: job_redis_channel={job_redis_channel}, redis_pub_message={redis_pub_message}")
                    try:
                        if job_redis_channel is not None and len(job_redis_channel) > 5 and redis_pub_message is not None:
                            print ( "Redis 발행 시도")
                            publisher = RedisPublisher()
                            구독자수 = publisher.publish(
                                channel=job_redis_channel, 
                                message= _create_redis_message(redis_pub_message)
                            )
                            print ( f"구독자수: {구독자수}")
                    except Exception as pub_error:
                        logger.error(f"Redis 발행 중 오류 (작업 완료): {pub_error}")   
                    
                    return result
                    
                except TimeoutError:
                    logger.warning(f"작업 타임아웃 발생: {timeout_seconds}초 초과")
                    print(f"[WRAPPER] 작업 타임아웃 발생: {timeout_seconds}초 초과")
                    
                    # 실행 시간 계산
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    # 작업 타임아웃 등록
                    logger.debug(f"작업 타임아웃 등록 시도: job_id={actual_job_id}")
                    print(f"[WRAPPER] 작업 타임아웃 등록 시도: job_id={actual_job_id}")
                    
                    unregister_running_job(actual_job_id, status='timeout')
                    logger.debug(f"작업 타임아웃 등록됨")
                    print(f"[WRAPPER] 작업 타임아웃 등록됨")
                    
                    # 타임아웃 로그 저장
                    logger.debug(f"타임아웃 로그 저장 시도")
                    print(f"[WRAPPER] 타임아웃 로그 저장 시도")
                    
                    log_entry = Scheduler_Job_Log.objects.create(
                        job_id=actual_job_id,
                        success=False,
                        log={"error": f"작업이 {timeout_seconds}초 내에 완료되지 않았습니다"},
                        execution_time_ms=execution_time_ms
                    )
                    logger.debug(f"타임아웃 로그 저장됨: {log_entry.id}")
                    print(f"[WRAPPER] 타임아웃 로그 저장됨: {log_entry.id}")
                    
                    raise TimeoutError(f"작업이 {timeout_seconds}초 내에 완료되지 않았습니다")
                    
                except Exception as e:
                    logger.error(f"작업 실행 중 예외 발생: {e}")
                    print(f"[WRAPPER] 작업 실행 중 예외 발생: {e}")
                    
                    # 실행 시간 계산
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    # 작업 오류 등록
                    logger.debug(f"작업 오류 등록 시도: job_id={actual_job_id}")
                    print(f"[WRAPPER] 작업 오류 등록 시도: job_id={actual_job_id}")
                    
                    unregister_running_job(actual_job_id, status='error')
                    logger.debug(f"작업 오류 등록됨")
                    print(f"[WRAPPER] 작업 오류 등록됨")
                    
                    # 오류 로그 저장
                    logger.debug(f"오류 로그 저장 시도")
                    print(f"[WRAPPER] 오류 로그 저장 시도")
                    
                    error_details = {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                    log_entry = Scheduler_Job_Log.objects.create(
                        job_id=actual_job_id,
                        success=False,
                        log=error_details,
                        execution_time_ms=execution_time_ms
                    )
                    logger.debug(f"오류 로그 저장됨: {log_entry.id}")
                    print(f"[WRAPPER] 오류 로그 저장됨: {log_entry.id}")
                    
                    raise
        
        except Exception as outer_e:
            logger.error(f"래퍼 함수 실행 중 오류: {outer_e}")
            logger.error(traceback.format_exc())
            print(f"[WRAPPER] 래퍼 함수 실행 중 오류: {outer_e}")
            print(traceback.format_exc())
            raise
    
    # 래핑된 함수에 추가 속성 설정
    wrapped_func.original_func = func
    wrapped_func.job_id = job_id
    wrapped_func.timeout_seconds = timeout_seconds
    
    # 래핑된 함수 반환 전 디버그 출력
    logger.debug(f"wrapped_func 생성 완료: {func.__name__}")
    print(f"[WRAPPER] wrapped_func 생성 완료: {func.__name__}")
    return wrapped_func 


def delete_old_job_executions(max_age=604_800):  # 기본값: 7일
    """오래된 작업 실행 기록 삭제"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

def get_scheduler():
    """APScheduler 인스턴스 반환"""
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # 스케줄러 설정
        scheduler._logger = logger  # 스케줄러 로거 설정
        
        # 스케줄러가 실행 중인지 확인하고 시작
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler 시작됨")
    elif not scheduler.running:
        # 기존 스케줄러가 있지만 실행 중이 아닌 경우 시작
        scheduler.start()
        logger.info("기존 APScheduler 다시 시작됨")
        
    return scheduler

def setup_jobs():
    """
    활성화된 모든 작업을 스케줄러에 등록
    """
    from scheduler_job.models import Scheduler_Job
    from django.utils.module_loading import import_string
    from scheduler_job.job_wrapper import job_wrapper_complete
    import logging
    
    logger = logging.getLogger('scheduler_job')
    
    # 스케줄러 가져오기
    scheduler = get_scheduler()
    
    # 기존 작업 제거 (선택 사항)
    # scheduler.remove_all_jobs()
    
    # 활성화된 작업 가져오기
    active_jobs = Scheduler_Job.objects.filter(is_active=True)
    
    # 각 작업을 스케줄러에 등록
    for job in active_jobs:
        try:
            # 작업 함수 가져오기
            job_function_str = job.job_info.job_function
            job_redis_channel = job.job_info.redis_channel
            logger.debug(f"작업 함수 문자열: {job_function_str}")
            logger.debug(f"작업 레디스 채널: {job_redis_channel}")
            job_function = import_string(job_function_str)
            logger.debug(f"작업 함수 가져옴: {job_function.__name__}")
            
            # 래핑된 함수 생성
            # wrapped_function = job_wrapper_complete(job_function, job.id, timeout_seconds=job.timeout_seconds)
            # logger.debug(f"래핑된 함수 생성됨: {job_function.__name__}")
            
            # 작업 유형에 따라 등록
            if job.job_type == 'interval':
                logger.debug(f"인터벌 작업 설정: {job.job_interval}초 간격")
                
                # 인터벌 작업 등록
                scheduler.add_job(
                    execute_job,
                    'interval',
                    seconds=job.job_interval,
                    id=f"job_{job.id}",
                    replace_existing=True,
                    args=[job_function_str, job.id, job.timeout_seconds],
                    kwargs={'job_redis_channel': job.job_info.redis_channel},
                    misfire_grace_time=60,
                    max_instances=1,
                    coalesce=True
                )
                print(f"인터벌 작업 설정 완료: {job.id} ({job.job_interval}초)")
                
            elif job.job_type == 'cron':
                # 크론 표현식 파싱
                cron_parts = job.cron_expression.split()
                if len(cron_parts) == 5:  # 표준 크론 표현식 (분 시 일 월 요일)
                    minute, hour, day, month, day_of_week = cron_parts
                # 크론 작업 등록
                scheduler.add_job(
                    execute_job,
                    'cron',
                    id=f"job_{job.id}",
                    replace_existing=True,
                    args=[job_function_str, job.id, job.timeout_seconds],
                    kwargs={'job_redis_channel': job.job_info.redis_channel},
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    misfire_grace_time=60,
                    max_instances=1,
                    coalesce=True,

                )
                print(f"크론 작업 설정 완료: {job.id} ({job.cron_expression})")
            
            logger.debug(f"추가된 작업: job_{job.id}, 함수: {job_function.__name__}")
            
        except Exception as e:
            logger.error(f"작업 {job.id} 설정 중 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # 작업 상태 모니터링 작업 추가
    # scheduler.add_job(
    #     monitor_job_status,
    #     'interval',
    #     minutes=5,
    #     id='monitor_job_status',
    #     replace_existing=True
    # )
    # print("작업 상태 모니터링 작업 추가됨")
    
    # 오래된 작업 정리 작업 추가
    scheduler.add_job(
        delete_old_job_executions,
        'interval',
        days=1,
        id='delete_old_job_executions',
        replace_existing=True
    )
    print("오래된 작업 정리 작업 추가됨")
    
    return scheduler