import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from logging.config import dictConfig


LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.INFO
# ColoredFormatter 클래스 추가
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[91m\033[1m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.COLORS['RESET']}"
    

#### file save는 하지 않음 : run worker 시 file 소유권 문제
def setup_logging(module_name:str='_logger', BASE_DIR=None):
    """
    Django 프로젝트의 로깅 설정을 구성합니다.
    
    Args:
        BASE_DIR: 프로젝트 기본 디렉토리 경로 ==> run worker 시 file 소유권 문제
        INSTALLED_APPS: Django 설정의 INSTALLED_APPS 리스트
    
    Returns:
        dict: Django settings.py에서 사용할 LOGGING 설정 딕셔너리
    """
    # 로그 디렉토리 생성
    if BASE_DIR is not None:
        logs_dir = os.path.join(BASE_DIR, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    
    # 환경에 따른 로그 레벨 설정
    default_level = LOG_LEVEL #if ENV == 'development' else 'INFO'
    
    # 기본 로거 설정
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{asctime} {levelname} {name} {module} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
            'colored': {
                '()': 'shapi.setting_log.ColoredFormatter',
                'format': '{asctime} {levelname} {name} {module} {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': default_level,
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
            # 'file': {
            #     'level': default_level,
            #     'class': 'logging.handlers.TimedRotatingFileHandler',
            #     'filename': os.path.join(logs_dir, 'django.log'),
            #     'when': 'midnight',
            #     'interval': 1,
            #     'backupCount': 30,
            #     'formatter': 'verbose',
            # },
            # 'error_file': {
            #     'level': 'ERROR',
            #     'class': 'logging.handlers.TimedRotatingFileHandler',
            #     'filename': os.path.join(logs_dir, 'error.log'),
            #     'when': 'midnight',
            #     'interval': 1,
            #     'backupCount': 30,
            #     'formatter': 'verbose',
            # },
        },
        'loggers': {
            'root': {
                'handlers': ['console'], # 'file', 'error_file'],
                'level': LOG_LEVEL,
                'propagate': True,  # 로그가 부모 로거로 전파될 수 있도록 설정
            },
            'django': {
                'handlers': ['console'], # 'file', 'error_file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'django.server': {
                'handlers': ['console'], # 'file', 'error_file'],
                'level': LOG_LEVEL,
                'propagate': True,  # 부모 로거로 로그 전파
            },
            'rest_framework': {
                'handlers': ['console'],  # 필요 시 'file', 'error_file'도 추가 가능
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            module_name : {
                'handlers': ['console'], # 'file', 'error_file'],
                'level': LOG_LEVEL,
                'propagate': True,
            },
        },
    }

    

    # # 설치된 앱별 로거 설정 (중요 앱만)
    # important_apps = []  # 여기에 중요한 앱 이름을 추가하세요
    
    # for app in INSTALLED_APPS:
    #     # Django 내장 앱 및 서드파티 앱 제외
    #     if app.startswith('django.') or app.startswith('rest_framework'):
    #         continue
            
    #     # 앱 이름 추출 (경로에서 마지막 부분만)
    #     app_name = app.split('.')[-1]
        
    #     # 앱별 로그 파일 핸들러 추가
    #     LOGGING['handlers'][f'{app_name}_file'] = {
    #         'level': 'DEBUG' if app_name in important_apps else default_level,
    #         'class': 'logging.handlers.TimedRotatingFileHandler',
    #         'filename': os.path.join(logs_dir, f'{app_name}.log'),
    #         'when': 'midnight',
    #         'interval': 1,
    #         'backupCount': 30,
    #         'formatter': 'verbose',
    #     }
        
    #     # 앱별 로거 추가
    #     LOGGING['loggers'][app_name] = {
    #         'handlers': ['console', f'{app_name}_file', 'error_file'],
    #         'level': 'DEBUG' if app_name in important_apps else default_level,
    #         'propagate': False,
    #     }
    
    dictConfig(logging_config)

    return logging_config


### scheulder_job 로그 정리로 넣을 것
def clean_old_logs(logs_dir, days_to_keep=30):
    """
    지정된 일수보다 오래된 로그 파일을 정리합니다.
    
    Args:
        logs_dir: 로그 디렉토리 경로
        days_to_keep: 유지할 로그 파일의 일수 (기본값: 30)
    """
    import glob
    import time
    from datetime import timedelta
    
    # 현재 시간에서 지정된 일수를 뺀 시간 계산
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    
    # 로그 디렉토리의 모든 로그 파일 검색
    log_files = glob.glob(os.path.join(logs_dir, '*.log.*'))
    
    for log_file in log_files:
        # 파일의 수정 시간 확인
        file_mod_time = os.path.getmtime(log_file)
        if file_mod_time < cutoff_time:
            try:
                os.remove(log_file)
                print(f"삭제된 오래된 로그 파일: {log_file}")
            except Exception as e:
                print(f"로그 파일 삭제 중 오류 발생: {e}")