from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from . import models as scheduler_job_models
from scheduler_job.setup_schedule import setup_scheduled_jobs



@receiver([post_save, post_delete], sender=scheduler_job_models.Scheduler_Job)
def clear_user_cache(sender, instance, **kwargs):
    """
    Scheduler_Job 모델이 변경되거나 삭제될 때 캐시를 초기화합니다
    """

    setup_scheduled_jobs()
