import time
import signal
import functools
from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log

class TimeoutError(Exception):
    """작업 타임아웃 예외"""
    pass

def timeout_handler(signum, frame):
    """시그널 핸들러: 타임아웃 발생 시 호출됨"""
    raise TimeoutError("작업이 제한 시간 내에 완료되지 않았습니다")

def with_timeout(seconds=30):
    """지정된 시간(초) 내에 함수 실행을 제한하는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # UNIX 시스템에서만 작동
            # Windows에서는 다른 방법 필요
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)  # 타이머 해제
        return wrapper
    return decorator

def measure_execution_time_with_timeout(timeout_seconds=30):
    """작업 실행 시간을 측정하고 타임아웃을 설정하는 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # job_id 인자 확인
            job_id = kwargs.get('job_id')
            
            # 시작 시간 기록
            start_time = time.time()
            
            try:
                # 타임아웃 설정
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)
                
                # 원래 함수 실행
                result = func(*args, **kwargs)
                
                # 타이머 해제
                signal.alarm(0)
                
                # 종료 시간 기록 및 실행 시간 계산 (밀리초 단위)
                end_time = time.time()
                execution_time_ms = int((end_time - start_time) * 1000)
                
                # 작업 ID가 제공된 경우 로그 저장
                if job_id:
                    job = Scheduler_Job.objects.get(id=job_id)
                    
                    # 결과를 JSON 형태로 변환
                    if isinstance(result, dict):
                        log_data = result.copy()
                    else:
                        log_data = {"result": result}
                    
                    # 실행 시간 추가
                    log_data["execution_time_ms"] = execution_time_ms
                    
                    # 로그 저장
                    Scheduler_Job_Log.objects.create(
                        job=job,
                        success=True,
                        log=log_data,
                        execution_time_ms=execution_time_ms
                    )
                
                return result
            
            except TimeoutError as e:
                # 타임아웃 발생 시
                end_time = time.time()
                execution_time_ms = int((end_time - start_time) * 1000)
                
                if job_id:
                    try:
                        job = Scheduler_Job.objects.get(id=job_id)
                        Scheduler_Job_Log.objects.create(
                            job=job,
                            success=False,
                            log={"error": f"타임아웃: {str(e)}", "timeout_seconds": timeout_seconds},
                            execution_time_ms=execution_time_ms
                        )
                    except Exception as inner_e:
                        print(f"로그 저장 중 오류 발생: {inner_e}")
                
                # 다음 작업 실행을 위해 예외를 잡음
                print(f"작업 타임아웃: {str(e)}")
                return {"error": "timeout", "message": str(e)}
                
            except Exception as e:
                # 기타 예외 발생 시
                signal.alarm(0)  # 타이머 해제
                
                end_time = time.time()
                execution_time_ms = int((end_time - start_time) * 1000)
                
                if job_id:
                    try:
                        job = Scheduler_Job.objects.get(id=job_id)
                        Scheduler_Job_Log.objects.create(
                            job=job,
                            success=False,
                            log={"error": str(e)},
                            execution_time_ms=execution_time_ms
                        )
                    except Exception as inner_e:
                        print(f"로그 저장 중 오류 발생: {inner_e}")
                
                # 예외 다시 발생
                raise
        
        return wrapper
    return decorator 