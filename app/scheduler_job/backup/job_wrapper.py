import logging
import functools
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from scheduler_job.job_manager import register_running_job, unregister_running_job
import sys

# 로거 설정
logger = logging.getLogger('scheduler_job')
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 추가 (매번 실행 시 확인)
def ensure_logger_has_handlers():
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

def job_wrapper_complete(func, job_id, timeout_seconds=30):
    """
    작업 함수를 래핑하여 다음 기능을 제공:
    1. 타임아웃 처리
    2. 실행 시간 측정
    3. 작업 상태 관리
    4. 결과 로깅
    """
    ensure_logger_has_handlers()
    logger.debug(f"job_wrapper_complete 정의됨: func={func.__name__}, job_id={job_id}")
    
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        ### 
        func()

        # 로거 핸들러 확인
        ensure_logger_has_handlers()
        
        from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log
        from scheduler_job.job_manager import register_running_job, unregister_running_job
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
                    logger.debug(f"작업 실행 시작: timeout={timeout_seconds}초")
                    print(f"[WRAPPER] 작업 실행 시작: timeout={timeout_seconds}초")
                    
                    result = future.result(timeout=timeout_seconds)
                    logger.debug(f"작업 실행 완료: {result}")
                    print(f"[WRAPPER] 작업 실행 완료: {result}")
                    
                    # 실행 시간 계산
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    # 작업 완료 등록
                    logger.debug(f"작업 완료 등록 시도: job_id={actual_job_id}")
                    print(f"[WRAPPER] 작업 완료 등록 시도: job_id={actual_job_id}")
                    
                    unregister_running_job(actual_job_id, status='completed')
                    logger.debug(f"작업 완료 등록됨")
                    print(f"[WRAPPER] 작업 완료 등록됨")
                    
                    # 성공 로그 저장
                    logger.debug(f"성공 로그 저장 시도")
                    print(f"[WRAPPER] 성공 로그 저장 시도")
                    
                    log_entry = Scheduler_Job_Log.objects.create(
                        job_id=actual_job_id,
                        success=True,
                        log=result,
                        execution_time_ms=execution_time_ms
                    )
                    logger.debug(f"성공 로그 저장됨: {log_entry.id}")
                    print(f"[WRAPPER] 성공 로그 저장됨: {log_entry.id}")
                    
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
