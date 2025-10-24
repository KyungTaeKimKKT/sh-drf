import os
import threading
import time
import signal
import logging
import traceback
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from scheduler_job.models import Scheduler_Job, Scheduler_Job_Status, Scheduler_Job_Log
from django_apscheduler.models import DjangoJobExecution

# 로거 설정
logger = logging.getLogger('scheduler_job')
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 추가
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# 실행 중인 작업 추적을 위한 전역 딕셔너리
running_jobs = {}

def register_running_job(job_id, thread=None, pid=None):
    """실행 중인 작업 등록"""
    job_key = str(job_id)
    running_jobs[job_key] = {
        'thread': thread or threading.current_thread(),
        'pid': pid or os.getpid(),
        'start_time': time.time()
    }
    
    # 데이터베이스에 상태 기록
    try:
        logger.debug(f"register_running_job: job_id={job_id} 상태 기록 시작")
        job = Scheduler_Job.objects.get(id=job_id)
        
        with transaction.atomic():
            status_record = Scheduler_Job_Status.objects.create(
                job=job,
                status='running',
                pid=running_jobs[job_key]['pid'],
                thread_id=str(running_jobs[job_key]['thread'].ident)
            )
            logger.debug(f"상태 기록 생성됨: {status_record.id}")
        
        running_jobs[job_key]['status_id'] = status_record.id
        return status_record
    except Exception as e:
        logger.error(f"작업 상태 등록 중 오류: {e}")
        logger.error(traceback.format_exc())
        raise

def unregister_running_job(job_id, status='completed'):
    """실행 중인 작업 등록 해제"""
    job_key = str(job_id)
    if job_key in running_jobs:
        # 실행 시간 계산
        start_time = running_jobs[job_key]['start_time']
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # 상태 기록 업데이트
        status_id = running_jobs[job_key].get('status_id')
        if status_id:
            try:
                logger.debug(f"unregister_running_job: status_id={status_id} 상태 업데이트 시작")
                with transaction.atomic():
                    status_record = Scheduler_Job_Status.objects.get(id=status_id)
                    status_record.end_time = timezone.now()
                    status_record.status = status
                    status_record.save()
                    logger.debug(f"상태 기록 업데이트됨: {status_record.id}")
            except Exception as e:
                logger.error(f"상태 기록 업데이트 중 오류: {e}")
                logger.error(traceback.format_exc())
        
        # 실행 중인 작업 목록에서 제거
        del running_jobs[job_key]
        
        return execution_time_ms
    return None

def terminate_job(job_id):
    """실행 중인 작업 강제 종료"""
    job_key = str(job_id)
    if job_key in running_jobs:
        job_info = running_jobs[job_key]
        
        try:
            # 프로세스 종료 시도
            os.kill(job_info['pid'], signal.SIGTERM)
            
            # 상태 업데이트
            unregister_running_job(job_id, status='terminated')
            
            # 로그 기록
            job = Scheduler_Job.objects.get(id=job_id)
            Scheduler_Job_Log.objects.create(
                job=job,
                success=False,
                log={"error": "작업이 강제 종료되었습니다"},
                execution_time_ms=int((time.time() - job_info['start_time']) * 1000)
            )
            
            return True
        except Exception as e:
            logger.error(f"작업 종료 중 오류: {e}")
            return False
    
    return False

def check_hanging_jobs(max_duration_seconds=600):
    """
    오래 실행 중인 작업을 확인하고 처리합니다
    """
    logger.debug(f"오래 실행 중인 작업 확인 중 (최대 실행 시간: {max_duration_seconds}초)")
    cutoff_time = timezone.now() - timezone.timedelta(seconds=max_duration_seconds)
    hanging_jobs = DjangoJobExecution.objects.filter(
        status=DjangoJobExecution.STARTED,
        start_time__lt=cutoff_time
    )
    
    logger.debug(f"오래 실행 중인 작업 수: {hanging_jobs.count()}")
    for job in hanging_jobs:
        logger.warning(f"오래 실행 중인 작업 처리: {job.job_id}, 시작 시간: {job.start_time}")
        job.status = DjangoJobExecution.ERROR
        job.save() 