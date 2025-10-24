from  django.db import transaction
from django.core.cache import cache
import time
from datetime import date, timedelta, datetime
import psutil
import logging, traceback
logger = logging.getLogger(__name__)

def get_system_resources():
    """
    시스템 리소스 정보를 수집하여 반환합니다.
    CPU(전체 및 코어별), 메모리, 네트워크 사용량 정보를 포함합니다.
    디스크 정보는 제외되었습니다.
    
    Returns:
        dict: 다음 구조를 가진 시스템 리소스 정보 딕셔너리
            {
                'cpu': {
                    'percent': float,  # CPU 전체 사용률 (%)
                    'count': int,      # CPU 코어 수 (논리적 코어 포함)
                    'cores': {         # 각 코어별 사용률
                        'core_0': float,  # 첫 번째 코어 사용률 (%)
                        'core_1': float,  # 두 번째 코어 사용률 (%)
                        # ... 추가 코어들
                    }
                },
                'memory': {
                    'total_gb': float,  # 전체 메모리 용량 (GB)
                    'used_gb': float,   # 사용 중인 메모리 (GB)
                    'percent': float    # 메모리 사용률 (%)
                },
                'network': {
                    'sent': str,     # 전송된 데이터 (MiB/s 또는 KiB/s)
                    'received': str,  # 수신된 데이터 (MiB/s 또는 KiB/s)
                    'sent_bytes_per_sec': int,  # 전송된 데이터 초당 바이트 수
                    'received_bytes_per_sec': int  # 수신된 데이터 초당 바이트 수
                },
                'processes': {
                    'count': int  # 실행 중인 프로세스 수
                },
                'timestamp': str  # 데이터 수집 시간 (YYYY-MM-DD HH:MM:SS 형식)
            }
        None: 오류 발생 시
    """
    result = {
        'cpu': {},
        'memory': {},
        'network': {},
        # 'processes': {},
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # CPU 정보 수집
    try:
        
        result['cpu']['percent'] = psutil.cpu_percent(interval=None)
        result['cpu']['count'] = psutil.cpu_count()
        cpu_cores_percent = psutil.cpu_percent(interval=None, percpu=True)
        result['cpu']['cores'] = {f'core_{i}': percent for i, percent in enumerate(cpu_cores_percent)}
    except Exception as e:
        logger.error(f"CPU 정보 수집 실패: {e}")
        result['cpu'] = {'error': str(e)}
    
    # 메모리 정보 수집
    try:
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 ** 3)  # GB 단위로 변환
        memory_used = memory.used / (1024 ** 3)
        result['memory'] = {
            'total': round(memory_total, 2),
            'used': round(memory_used, 2),
            'percent': memory.percent
        }
    except Exception as e:
        logger.error(f"메모리 정보 수집 실패: {e}")
        result['memory'] = {'error': str(e)}
    
    # 네트워크 정보 수집
    try:
        # 현재 측정
        net_io_current = psutil.net_io_counters()
        current_time = datetime.now()
        
        # Redis 캐시에서 이전 측정값 가져오기
        previous_data = cache.get('network_io')
        if previous_data:
            previous_bytes_sent = previous_data['bytes_sent']
            previous_bytes_recv = previous_data['bytes_recv']
            previous_timestamp = datetime.fromisoformat(previous_data['timestamp'])
            
            # 이전 측정값과의 차이 계산
            time_diff = (current_time - previous_timestamp).total_seconds()
            if time_diff > 0:
                sent_per_sec = (net_io_current.bytes_sent - previous_bytes_sent) / (time_diff * 1024 * 1024)
                recv_per_sec = (net_io_current.bytes_recv - previous_bytes_recv) / (time_diff * 1024 * 1024)
            else:
                sent_per_sec = 0
                recv_per_sec = 0
        else:
            # 이전 데이터가 없을 경우
            sent_per_sec = 0
            recv_per_sec = 0
        
        result['network'] = {
            'sent': round(sent_per_sec, 2),
            'received': round(recv_per_sec, 2)
        }
        
        # 현재 측정값을 Redis 캐시에 저장
        cache.set('network_io', {
            'bytes_sent': net_io_current.bytes_sent,
            'bytes_recv': net_io_current.bytes_recv,
            'timestamp': current_time.isoformat()
        })
    except Exception as e:
        logger.error(f"네트워크 정보 수집 실패: {e}")
        result['network'] = {'error': str(e)}
    
    # 프로세스 정보 수집
    # try:
    #     process_count = 0
    #     for _ in psutil.process_iter(['pid']):  # 필요한 정보만 요청
    #         process_count += 1
    #     result['processes'] = {'count': process_count}
    # except Exception as e:
    #     logger.error(f"프로세스 정보 수집 실패: {e}")
    #     result['processes'] = {'error': str(e)}
    
    return result

def main_job(job_id:int):
    s = time.time()

    try:
        resources = get_system_resources()
        if resources:
            # CPU 코어별 정보 로그 문자열 생성
            cores_log = ", ".join([f"코어{i}: {percent}%" for i, percent in enumerate(resources['cpu']['cores'].values())])
            
            return {
                'log': f"시스템 리소스 모니터링 완료: CPU 전체 {resources['cpu']['percent']}%, {cores_log}, 메모리 {resources['memory']['percent']}% - 소요시간: {int((time.time() - s) * 1000)} msec",
                'redis_publish': resources
            }
        else:
            return {
                'log': "시스템 리소스 정보 수집 실패",
                'redis_publish': None
            }
    except Exception as e:
        logger.error(f"시스템 리소스 모니터링 실패: {e}")
        logger.error(traceback.format_exc())
        return {
            'log': f"시스템 리소스 모니터링 실패: {e}",
            'redis_publish': None
        }

