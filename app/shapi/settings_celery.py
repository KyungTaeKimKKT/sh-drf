# Redis 설정을 settings.py와 일치시키기
import os

# Celery 설정
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'  # 한국 시간대 설정

# django-celery-beat 설정
# INSTALLED_APPS_CELERY = ['django_celery_beat']

# Celery Beat 스케줄러 설정
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# 태스크 라우팅 설정
CELERY_TASK_ROUTES = {
    'users.tasks.*': {'queue': 'users'},
    'scheduler_job.tasks.*': {'queue': 'scheduler'},
    '모니터링.tasks.*': {'queue': 'monitoring'},
    # 기본 큐는 'celery'
}

# 태스크 기본 설정
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'

# 태스크 시간 제한 설정
CELERY_TASK_TIME_LIMIT = 60 * 5  # 5분
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 3  # 3분

# 워커 설정
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # 워커가 재시작하기 전에 처리할 최대 태스크 수
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # 워커가 한 번에 가져올 태스크 수

# 결과 백엔드 설정
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # 결과 만료 시간 (24시간)




# Beat 스케줄 설정
# from celery.schedules import timedelta, crontab

# CELERY_BEAT_SCHEDULE = {
#     # 생산모니터링 작업 (10초마다)
#     # 'production-monitoring': {
#     #     'task': 'scheduler_job.tasks.execute_scheduled_job',
#     #     'schedule': timedelta(seconds=10),
#     #     'args': (3,),  # 생산모니터링 작업 ID
#     #     'options': {
#     #         'queue': 'scheduler',
#     #     },
#     # },
#     # 정부기관 스크래핑 작업 (크론 표현식)
#     'government-scraping': {
#         'task': 'scheduler_job.tasks.execute_scheduled_job',
#         'schedule': crontab(minute='*', hour='7-23'),
#         'args': (5,),  # 정부기관 스크래핑 작업 ID
#         'options': {
#             'queue': 'scheduler',
#         },
#     },
# }