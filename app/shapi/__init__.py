# 이 파일은 Django가 시작될 때 자동으로 임포트됩니다
from shapi.celery import app as celery_app

__all__ = ('celery_app',)


