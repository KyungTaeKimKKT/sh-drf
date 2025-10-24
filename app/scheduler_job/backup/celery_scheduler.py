from celery import Celery
# from celery.schedules import crontab, schedule
import celery.schedules as celery_schedules
from django.conf import settings
from .models import Scheduler_Job
from .tasks import execute_scheduled_job
from datetime import timedelta
import logging
import traceback
logger = logging.getLogger('celery_scheduler')

def reset_celery_beat_schedule(app):
    """기존 스케줄을 모두 제거하고 새로 설정합니다"""
    # 기존 스케줄 초기화
    print("기존 스케줄:")
    for task_name, task_info in app.conf.beat_schedule.items():
        print(f"- {task_name}: {task_info}")
    
    # 스케줄 완전 초기화
    app.conf.beat_schedule = {}
    
    # 새 스케줄 설정
    app.conf.beat_schedule = get_scheduled_jobs()
    
    # 디버깅용 로그
    print("스케줄이 재설정되었습니다:")
    for task_name, task_info in app.conf.beat_schedule.items():
        print(f"- {task_name}: {task_info['schedule']}")

def get_scheduled_jobs():
    """활성화된 스케줄러 작업을 Celery Beat 스케줄로 변환"""
    # logger.info("get_scheduled_jobs 호출됨")
    beat_schedule = {}
    
    # 활성화된 작업 가져오기
    active_jobs = Scheduler_Job.objects.filter(is_active=True, job_info__is_active=True)

    # logger.info(f"활성화된 작업 수: {active_jobs.count()}")
    
    # print(f"활성화된 작업 수: {active_jobs.count()}")
    
    for job in active_jobs:
        task_name = f"job_{job.id}_{job.job_info.name}"
        # logger.info(f"작업 설정: {task_name}, 타입: {job.job_type}, 간격: {job.job_interval}")
        
        if job.job_type == 'interval':
            # 인터벌 작업 설정 - timedelta 사용
            beat_schedule[task_name] = {
                'task': 'scheduler_job.tasks.execute_scheduled_job',
                'schedule': timedelta(seconds=job.job_interval),
                'args': (job.id,),
            }
        elif job.job_type == 'cron':
            # 크론 작업 설정 (크론 표현식 파싱 필요)
            try:
                cron_parts = job.cron_expression.split()
                if len(cron_parts) == 5:
                    minute, hour, day_of_month, month_of_year, day_of_week = cron_parts
                    beat_schedule[task_name] = {
                        'task': 'scheduler_job.tasks.execute_scheduled_job',
                        'schedule': celery_schedules.crontab(
                            minute=minute,
                            hour=hour,
                            day_of_month=day_of_month,
                            month_of_year=month_of_year,
                            day_of_week=day_of_week
                        ),
                        'args': (job.id,),
                    }
                else:
                    # 크론 표현식 형식이 잘못된 경우 로깅
                    print(f"잘못된 크론 표현식 형식: {job.cron_expression} (작업 ID: {job.id})")
            except Exception as e:
                # 크론 표현식 파싱 중 오류 발생 시 로깅
                print(f"크론 표현식 파싱 오류: {str(e)} (작업 ID: {job.id})")
    
    print("최종 스케줄:")
    for name, config in beat_schedule.items():
        print(f"- {name}: {config}")
    
    return beat_schedule

# Celery Beat 설정을 동적으로 업데이트하는 함수
def update_celery_beat_schedule(app):
    # logger.info("update_celery_beat_schedule 호출됨")
    app.conf.beat_schedule = get_scheduled_jobs()
    # logger.info("Celery Beat 스케줄이 업데이트되었습니다.")
