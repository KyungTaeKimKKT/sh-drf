import threading
import time
import functools
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def run_with_timeout(func, args=None, kwargs=None, timeout_seconds=30):
    """
    지정된 시간 내에 함수를 실행하고, 타임아웃 시 예외를 발생시킵니다.
    Windows와 Unix 모두 호환됩니다.
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except TimeoutError:
            raise TimeoutError(f"함수 {func.__name__}이(가) {timeout_seconds}초 내에 완료되지 않았습니다")

def job_wrapper_with_timeout(func, job_id, timeout_seconds=30):
    """작업 함수를 래핑하여 타임아웃과 실행 시간을 측정하는 함수"""
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log
        
        # 시작 시간 기록
        start_time = time.time()
        
        try:
            # 타임아웃과 함께 함수 실행
            result = run_with_timeout(
                func=func,
                args=args,
                kwargs=kwargs,
                timeout_seconds=timeout_seconds
            )
            
            # 종료 시간 기록 및 실행 시간 계산 (밀리초 단위)
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)
            
            # 결과 저장
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
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)
            
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
    
    return wrapped_func 