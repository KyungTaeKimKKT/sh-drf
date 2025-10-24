from django.db import models, transaction
from django.conf import settings
from config.models import WS_URLS_DB

class JOB_INFO(models.Model):
    """개발자 영역임"""
    name = models.CharField(max_length=250,  default='job_name')
    job_function = models.CharField(max_length=250, default='scheduler_job.tasks.test_job')
    description = models.TextField(default='description')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    ws_url_db = models.ForeignKey(WS_URLS_DB, on_delete=models.CASCADE, 
                                 null=True, blank=True, related_name='ws_url_db_set')

    def __str__(self):
        return self.name
    
    @property
    def ws_url_name(self)->str|None:
        if self.ws_url_db:
            return f"{self.ws_url_db.group}/{self.ws_url_db.channel}".strip()
        return None

    @property
    def redis_channel(self)->str|None:
        if self.ws_url_db:
            return f"{self.ws_url_db.group}:{self.ws_url_db.channel}".strip()
        return None


class Scheduler_Job(models.Model):
    """스케줄러 작업에 대한  모델"""
    TYPE_CHOICES = [
        ('interval', '인터벌(초 단위 실행)'),
        ('cron', '크론(특정 시간 실행)'),
    ]
    job_info = models.ForeignKey(JOB_INFO, on_delete=models.CASCADE, null=True, blank=True, related_name='job_info_set')
    job_type = models.CharField(max_length=250, choices=TYPE_CHOICES, default='interval')

    job_interval = models.IntegerField(default=1)
    cron_expression = models.CharField(max_length=250, default='cron_expression')

    timeout_seconds = models.IntegerField(default=300, help_text="작업 타임아웃 시간(초)")
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    end_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    created_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_by_set', null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='updated_by_set', null=True, blank=True )

    is_db_log = models.BooleanField(default=False)
    is_db_status = models.BooleanField(default=False)

class Scheduler_Job_Status(models.Model):
    job = models.ForeignKey('Scheduler_Job', on_delete=models.CASCADE, related_name='status_records')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('running', '실행 중'),
        ('completed', '완료됨'),
        ('failed', '실패'),
        ('timeout', '타임아웃'),
        ('terminated', '강제 종료')
    ], default='running')
    pid = models.IntegerField(null=True, blank=True)  # 프로세스 ID
    thread_id = models.CharField(max_length=50, null=True, blank=True)  # 스레드 ID
    
    class Meta:
        ordering = ['-start_time']


class Scheduler_Job_Log(models.Model):
    """스케줄러 작업 로그에 대한  모델"""
    job = models.ForeignKey(Scheduler_Job, on_delete=models.CASCADE)
    success = models.BooleanField(default=False)
    log = models.JSONField(default= {})
    execution_time_ms = models.IntegerField(default=0, help_text='작업 소요 시간(msec)') ### 
    created_time = models.DateTimeField(auto_now_add=True)
