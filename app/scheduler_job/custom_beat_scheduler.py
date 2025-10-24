#### shapi/settings.py 에서 설정되어 있음. 
### (CELERY_BEAT_SCHEDULER = 'scheduler_job.custom_beat_scheduler.CustomDatabaseScheduler') CustomDatabaseScheduler 사용
from celery.beat import Scheduler
import celery.schedules as celery_schedules
from datetime import datetime, timedelta
# from .celery_scheduler import get_scheduled_jobs, update_celery_beat_schedule
from .models import Scheduler_Job
from .tasks import execute_scheduled_job

import traceback,logging
logger = logging.getLogger(__name__)

class CustomDatabaseScheduler(Scheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_schedules()

    def update_schedules(self):
        # 기존 스케줄을 초기화하고 새로 설정
        self.app.conf.beat_schedule = self.get_scheduled_jobs()

    def tick(self):
        # 주기적으로 스케줄을 업데이트 : 현재 1초
        self.update_celery_beat_schedule(self.app)
        return super().tick() 
    
    # def tick(self, *args, **kwargs):
    #     due_in = super().tick(*args, **kwargs)
    #     # 최소 1초, 최대 60초 간격으로 DB 재조회
    #     return max(1.0, min(due_in, 60.0))

    def sync(self):
        # 스케줄을 동기화하는 메서드
        self.update_schedules()

    # Celery Beat 설정을 동적으로 업데이트하는 함수
    def update_celery_beat_schedule(self, app):
        """Celery Beat 설정을 동적으로 업데이트하는 함수"""
        self._set_beat_schedule(app)

    def reset_celery_beat_schedule(self, app):
        """기존 스케줄을 모두 제거하고 새로 설정합니다"""
        # 기존 스케줄 초기화
        for task_name, task_info in app.conf.beat_schedule.items():
            logger.info(f"- {task_name}: {task_info}")
        
        # 스케줄 완전 초기화
        app.conf.beat_schedule = {}
        
        # 새 스케줄 설정
        self._set_beat_schedule(app)

    def _set_beat_schedule(self, app):
        """스케줄을 설정하는 내부 메서드"""
        app.conf.beat_schedule = self.get_scheduled_jobs()
        logger.info("스케줄이 설정되었습니다:")
        for task_name, task_info in app.conf.beat_schedule.items():
            logger.info(f"- {task_name}: {task_info['schedule']}")

    def get_scheduled_jobs(self):
        """활성화된 스케줄러 작업을 Celery Beat 스케줄로 변환"""
        # logger.info("get_scheduled_jobs 호출됨")
        beat_schedule = {}
        
        # 활성화된 작업 가져오기
        active_jobs = Scheduler_Job.objects.filter(
            is_active=True, job_info__is_active=True
            )

        # logger.info(f"활성화된 작업 수: {active_jobs.count()}")
        
        logger.info(f"활성화된 작업 수: {active_jobs.count()}")
        
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
                        logger.info(f"잘못된 크론 표현식 형식: {job.cron_expression} (작업 ID: {job.id})")
                except Exception as e:
                    # 크론 표현식 파싱 중 오류 발생 시 로깅
                    logger.info(f"크론 표현식 파싱 오류: {str(e)} (작업 ID: {job.id})")
        
        logger.info("최종 스케줄:")
        for name, config in beat_schedule.items():
            logger.info(f"- {name}: {config}")
        
        return beat_schedule