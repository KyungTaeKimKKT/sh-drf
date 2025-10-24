from __future__ import absolute_import, unicode_literals
from django.conf import settings
import os
import atexit
from datetime import timedelta
import logging
import sys

# 로거 설정 직접 구성
def setup_beat_logger():
    logger = logging.getLogger('celery_beat')
    logger.setLevel(logging.ERROR)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 파일 핸들러 => 제외함.
    # try:
    #     logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    #     if not os.path.exists(logs_dir):
    #         os.makedirs(logs_dir)
        
    #     file_handler = logging.FileHandler(os.path.join(logs_dir, 'celery_beat.log'))
    #     file_handler.setLevel(logging.INFO)
    #     file_handler.setFormatter(formatter)
        
    #     # 핸들러 추가
    #     logger.addHandler(file_handler)
    # except Exception as e:
    #     print(f"파일 로거 설정 중 오류: {e}")
    
    logger.addHandler(console_handler)
    return logger

from django import setup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shapi.settings")
# setup()  # This ensures that Django is fully set up before doing anything
# 로거 설정
beat_logger = setup_beat_logger()


from celery import Celery

# Celery 앱 생성
app = Celery('shapi')



# Django 설정에서 Celery 관련 설정 가져오기 (CELERY_ 접두사가 붙은 설정)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 작업 자동 검색
app.autodiscover_tasks()
