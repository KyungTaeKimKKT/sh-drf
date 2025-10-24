import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class JobWrapper:
    """작업 래퍼 클래스"""
    
    def __init__(self, func, job_id, timeout_seconds=30):
        self.func = func
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds
        print(f"[DEBUG] JobWrapper 초기화: func={func.__name__}, job_id={job_id}")
    
    def __repr__(self):
        return f"<JobWrapper for {self.func.__name__} (job_id={self.job_id})>"
    
    # 클래스 자체가 호출될 때 처리
    @classmethod
    def __new__(cls, *args, **kwargs):
        if len(args) >= 3:  # func, job_id, timeout_seconds
            # 일반적인 인스턴스 생성
            return super().__new__(cls)
        else:
            # APScheduler에서 직접 호출될 때
            print(f"[DEBUG] JobWrapper 클래스가 직접 호출됨: args={args}, kwargs={kwargs}")
            # 기본 인스턴스 생성 후 __call__ 호출
            instance = cls.__instances.get(kwargs.get('job_id'))
            if instance:
                return instance(*args, **kwargs)
            else:
                print(f"[ERROR] job_id={kwargs.get('job_id')}에 대한 JobWrapper 인스턴스를 찾을 수 없습니다.")
                raise ValueError(f"JobWrapper 인스턴스를 찾을 수 없습니다: job_id={kwargs.get('job_id')}")
    
    # 인스턴스 저장을 위한 클래스 변수
    __instances = {}
    
    # 인스턴스 등록
    def register(self):
        JobWrapper.__instances[self.job_id] = self
        return self
        
    def __call__(self, *args, **kwargs):
        from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log
        from scheduler_job.job_manager import register_running_job, unregister_running_job
        
        print(f"[DEBUG] JobWrapper.__call__ 호출됨: args={args}, kwargs={kwargs}")
        
        # kwargs에서 job_id 확인
        passed_job_id = kwargs.get('job_id')
        print(f"[DEBUG] 전달된 job_id: {passed_job_id}, 저장된 job_id: {self.job_id}")
        
        # 실제 사용할 job_id 결정
        actual_job_id = passed_job_id if passed_job_id is not None else self.job_id
        
        try:
            # 작업 시작 등록
            status_record = register_running_job(actual_job_id)
            print(f"[DEBUG] 작업 상태 등록됨: {status_record}")
            
            # 시작 시간 기록
            start_time = time.time()
            
            # 스레드 풀을 사용한 타임아웃 처리
            with ThreadPoolExecutor(max_workers=1) as executor:
                print(f"[DEBUG] ThreadPoolExecutor 생성됨")
                
                # kwargs에서 job_id 제거 (원래 함수에 전달하지 않음)
                func_kwargs = kwargs.copy()
                if 'job_id' in func_kwargs and 'job_id' not in self.func.__code__.co_varnames:
                    print(f"[DEBUG] kwargs에서 job_id 제거")
                    del func_kwargs['job_id']
                
                future = executor.submit(self.func, *args, **func_kwargs)
                print(f"[DEBUG] future 생성됨: {future}")
                
                try:
                    # 지정된 시간 내에 작업 완료 대기
                    print(f"[DEBUG] future.result() 호출, timeout={self.timeout_seconds}")
                    result = future.result(timeout=self.timeout_seconds)
                    print(f"[DEBUG] result 생성됨: {result}")
                    
                    # 종료 시간 기록 및 실행 시간 계산 (밀리초 단위)
                    end_time = time.time()
                    execution_time_ms = int((end_time - start_time) * 1000)
                    print(f"[DEBUG] 실행 시간: {execution_time_ms}ms")
                    
                    # 작업 완료 등록
                    unregister_running_job(actual_job_id, status='completed')
                    print(f"[DEBUG] 작업 완료 등록됨")
                    
                    # 결과 저장
                    try:
                        job = Scheduler_Job.objects.get(id=actual_job_id)
                        print(f"[DEBUG] 작업 조회됨: {job}")
                        
                        # 결과를 JSON 형태로 변환
                        if isinstance(result, dict):
                            log_data = result.copy()
                        else:
                            log_data = {"result": str(result)}
                        
                        # 실행 시간 추가
                        log_data["execution_time_ms"] = execution_time_ms
                        print(f"[DEBUG] 로그 데이터: {log_data}")
                        
                        # 로그 저장
                        log_entry = Scheduler_Job_Log.objects.create(
                            job=job,
                            success=True,
                            log=log_data,
                            execution_time_ms=execution_time_ms
                        )
                        print(f"[DEBUG] 로그 저장됨: {log_entry.id}")
                    except Exception as db_error:
                        print(f"[ERROR] 데이터베이스 작업 중 오류: {db_error}")
                        print(traceback.format_exc())
                    
                    return result
                    
                except TimeoutError:
                    # 타임아웃 발생 시
                    print(f"[ERROR] 작업 {actual_job_id} 타임아웃: {self.timeout_seconds}초 초과")
                    end_time = time.time()
                    execution_time_ms = int((end_time - start_time) * 1000)
                    
                    # 작업 타임아웃 등록
                    unregister_running_job(actual_job_id, status='timeout')
                    
                    # 로그 저장
                    try:
                        job = Scheduler_Job.objects.get(id=actual_job_id)
                        Scheduler_Job_Log.objects.create(
                            job=job,
                            success=False,
                            log={"error": f"타임아웃: 작업이 {self.timeout_seconds}초 내에 완료되지 않았습니다"},
                            execution_time_ms=execution_time_ms
                        )
                    except Exception as inner_e:
                        print(f"[ERROR] 로그 저장 중 오류: {inner_e}")
                    
                    return {"error": "timeout", "message": f"작업이 {self.timeout_seconds}초 내에 완료되지 않았습니다"}
                    
                except Exception as e:
                    # 기타 예외 발생 시
                    print(f"[ERROR] 작업 {actual_job_id} 실행 중 오류: {e}")
                    print(traceback.format_exc())
                    end_time = time.time()
                    execution_time_ms = int((end_time - start_time) * 1000)
                    
                    # 작업 실패 등록
                    unregister_running_job(actual_job_id, status='failed')
                    
                    # 로그 저장
                    try:
                        job = Scheduler_Job.objects.get(id=actual_job_id)
                        Scheduler_Job_Log.objects.create(
                            job=job,
                            success=False,
                            log={"error": str(e)},
                            execution_time_ms=execution_time_ms
                        )
                    except Exception as inner_e:
                        print(f"[ERROR] 로그 저장 중 오류: {inner_e}")
                    
                    raise
        
        except Exception as outer_e:
            print(f"[ERROR] 래퍼 실행 중 오류: {outer_e}")
            print(traceback.format_exc())
            raise 