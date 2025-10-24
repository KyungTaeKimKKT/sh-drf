from . import models as scheduler_job_models
from redis import Redis
from django_rq import get_scheduler
from datetime import datetime, timedelta
from rq_scheduler import Scheduler

def setup_scheduled_jobs():
    """
    setup scheduled jobs
    """
    redis_conn = Redis()
    scheduler = get_scheduler(connection=redis_conn)
    print('setup_scheduled_jobs start')
    # 기존 스케줄 삭제
    for job in scheduler.get_jobs():
        try:
            job.cancel()
        except Exception as e:
            print(f'{job.id} job cancel error:',e)

    for job in scheduler_job_models.Scheduler_Job.objects.filter(is_active=True):
        print('job:',job)
        
        # job_info 객체에서 job_function 가져오기
        job_function = job.job_info.job_function
        print(job_function)
        print(job.job_interval)
        
        if job.job_type == 'interval':
            # 인터벌 작업 스케줄링
            scheduler.schedule(
                scheduled_time=datetime.utcnow() + timedelta(seconds=job.job_interval),  # 시작 시간
                func=job_function,
                interval= job.job_interval,  # 초 단위 간격
                repeat=None,  # 무한 반복
                id=str(job.id)  # job_id는 문자열이어야 함
            )

        elif job.job_type == 'cron':
            # 크론 작업 스케줄링
            scheduler.cron(
                cron_string=job.cron_expression,
                func=job_function,
                id=str(job.id)  # job_id는 문자열이어야 함
            )