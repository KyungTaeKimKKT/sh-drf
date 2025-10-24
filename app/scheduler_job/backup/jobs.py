# from django_rq import job
from scheduler_job.models import Scheduler_Job, Scheduler_Job_Log
from functools import wraps
from datetime import datetime, date, time, timedelta
import traceback
import json
import time
from  django.core.cache import cache

def task_wrapper(func, job_id):
    """작업 함수를 래핑하여 실행 시간을 측정하고 결과를 저장하는 함수"""
    @wraps(func)
    def wrapped_func(*args, **kwargs):
        duration = 0
        start_time = time.time()
        try:
            # 원래 함수 실행
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = int((end_time - start_time) * 1000)

            if isinstance(result, dict):
                log_data = result
            elif hasattr(result, '__dict__'):  # 객체인 경우 __dict__ 속성 사용
                log_data = {"result": result.__dict__}
            else:
                # 기본 타입(문자열, 숫자, 리스트 등)
                log_data = {"result": result}
    
            # JSON 직렬화 가능 여부 확인
            import json
            json.dumps(log_data)  # 테스트용 직렬화
            
            # 결과 저장
            job = Scheduler_Job.objects.get(id=job_id)
            Scheduler_Job_Log.objects.create(
                job=job,
                success=True,
                log = log_data,
                duration = duration
            )
            
        except TypeError as e:
            # JSON으로 직렬화할 수 없는 객체 처리
            Scheduler_Job_Log.objects.create(
                job=job,
                success=True,
                log={"result": str(result), 
                     "error": f"원본 결과를 JSON으로 변환할 수 없음: {str(e)}"},  
                duration = duration
            )
        except Exception as e:
            # 기타 예외 처리
            Scheduler_Job_Log.objects.create(
                job=job,
                success=False,
                log={"error": f"로그 저장 중 오류 발생: {str(e)}"},
                duration = duration
            )
    
    return wrapped_func
# @job
def test_job(job_id):
   
    print(f"[TEST] test_job 실행 시작, job_id={job_id} , {datetime.now()} ")
    
    result = {
        "status": "completed",
        "message": f"테스트 작업 완료 (job_id: {job_id})",
        "timestamp": time.time()
    }
    
    print(f"[TEST] test_job 실행 완료, 결과: {result}")
    return result


import 생산모니터링.models_외부 as Models_외부 
import 생산모니터링.models as Models_내부
def 생산실적_실시간_모니터링(job_id):
    """ 생산계획실적 실시간 모니터링 """

    def fetch_휴식시간() -> list[dict]:
        """ 휴식시간 목록 조회 """
        cache_key = '휴식시간_목록'
        휴식시간_list = cache.get(cache_key)
        if 휴식시간_list is None:
            휴식시간_list = Models_내부.휴식시간_DB.objects.all().values('적용대상', '휴식시간_시작', '휴식시간_종료')
            cache.set(cache_key, 휴식시간_list, timeout=60*60*1)

        return 휴식시간_list

    def fetch_생산계획() -> list[dict]:
        """ 생산계획 목록 조회 """
        cache_key = '생산계획_목록'
        생산계획_list = cache.get(cache_key)
        if 생산계획_list is None:
            생산계획_list = ( Models_외부.생산계획실적.objects.using('생산모니터링').
                         filter(start_time__contains=date.today() ).order_by('sensor_id')
                         .values() )
            생산계획_list =[{**항목, 'start_time': 항목['start_time'].time(), 'end_time': 항목['end_time'].time()} for 항목 in 생산계획_list]
            cache.set(cache_key, 생산계획_list, timeout=60*60*1)

        return 생산계획_list
    
    def get_sensor별_휴식시간list( 휴식시간_list:list[dict] ) -> dict:
        """ 센서별 휴식시간 목록 조회 """
        #결과를 저장할 딕셔너리
        센서별_휴식시간 = {}

        # 데이터 변환
        for 항목 in 휴식시간_list:
            센서_목록 = 항목['적용대상'].split(',')
            휴식시간 = ( 항목['휴식시간_시작'], 항목['휴식시간_종료'] )
            
            # 각 센서에 휴식시간 추가
            for 센서 in 센서_목록:
                if 센서 in 센서별_휴식시간:
                    센서별_휴식시간[센서].append(휴식시간)
                else:
                    센서별_휴식시간[센서] = [휴식시간]
        return 센서별_휴식시간
    
    def get_sensor_기준정보() -> dict:
        """ 센서 기준정보 조회 """
        cache_key = 'sensor_기준정보'
        sensor_기준정보_dict = cache.get(cache_key)
        if sensor_기준정보_dict is None:
            sensor_기준정보_qs = Models_외부.sensor_기준정보.objects.using('생산모니터링').values('sensor_id', 'tact_time')
            sensor_기준정보_dict = { _dict['sensor_id'] : _dict['tact_time'] for _dict in sensor_기준정보_qs }
            cache.set(cache_key, sensor_기준정보_dict, timeout=60*60*1)
        return sensor_기준정보_dict

    def get_예상생산_time(생산계획실적_list: list[dict], sensor_기준정보_dict: dict , sensor_별_휴식시간_list: dict ) -> dict[str, list[datetime.time]]:
        """ 예상생산시간 계산 """
        cache_key = '예상생산시간_목록'
        예상생산_time  = cache.get(cache_key)
        if 예상생산_time and isinstance(예상생산_time, dict) and len(예상생산_time.keys()) == len(생산계획실적_list):
            return 예상생산_time
        
        예상생산_time = {}
        for _dict in 생산계획실적_list:
            sensor_id = _dict['sensor_id']
            tact_time = sensor_기준정보_dict[sensor_id]
            start_time = _dict['start_time']
            end_time = _dict['end_time']    
            예상생산_time_list = [start_time]
            # time 객체를 오늘 날짜의 datetime 객체로 변환
            today = date.today()
            current_dt = datetime.combine(today, start_time)
            end_dt = datetime.combine(today, end_time)
            
            while current_dt.time() < end_time:
                current_dt += timedelta(seconds=tact_time)
                _isIn, 휴식시간_종료 = _in_휴식시간(current_dt.time(), sensor_별_휴식시간_list.get(sensor_id, []))
                if _isIn:
                    # 휴식시간_종료도 datetime으로 변환하여 연산
                    current_dt = datetime.combine(today, 휴식시간_종료) + timedelta(seconds=tact_time)
                예상생산_time_list.append(current_dt.time())
        
            예상생산_time[sensor_id] = 예상생산_time_list
        cache.set(cache_key, 예상생산_time, timeout=60*60*1)
            # _dict['예상생산_time_list'] = 예상생산_time_list
        return 예상생산_time

    def get_max_생산량( 생산계획_dict:dict, sensor_기준정보_dict:dict ) -> dict:
        """ 생산계획 목록에서 최대 생산량 계산 """
        for _instance in 생산계획_dict:
            sensor_id = _instance['sensor_id']
            tact_time = sensor_기준정보_dict[sensor_id]
            max_생산량 = _instance['생산량'] / tact_time
            _instance['max_생산량'] = max_생산량
        return 생산계획_dict

    def _in_휴식시간( 예상생산_time:datetime.time, 휴식시간_list:list[tuple[datetime.time, datetime.time]] ) -> tuple[bool, datetime.time]:
        """ 예상생산시간이 휴식시간에 포함되는지 여부 확인 """
        for 휴식시간 in 휴식시간_list:
            if 예상생산_time >= 휴식시간[0] and 예상생산_time <= 휴식시간[1]:
                return True, 휴식시간[1]
        return False, None
    
    def _get_달성률( obj:dict ) -> float:
        return float("{:.1f}".format(obj.get('job_qty') / obj.get('plan_qty') * 100)) if obj.get('plan_qty') else obj.get('plan_qty')

    def _get_운영tt( obj:dict ) -> int:
        """ 운영tt 계산 """
        start_time = obj.get('start_time')  
        job_qty_time = obj.get('job_qty_time')
        start_time = datetime.combine(date.today(), start_time)

        tt_시작시간:datetime = job_qty_time if ( job_qty_time < start_time) else  start_time

        운영tt = int( (datetime.now() -tt_시작시간).total_seconds() )
        return 운영tt

    def _get_이론생산량(예상시간List: list[datetime.time], curTime: datetime.time = datetime.now().time()) -> int:
        """
        정렬된 시간 리스트에서 기준_시간보다 크거나 같은 첫 번째 요소의 인덱스를 반환합니다.
        만약 기준_시간이 모든 요소보다 크다면 마지막 인덱스를 반환합니다.
        """
        for i, 시간 in enumerate(예상시간List):
            if 시간 >= curTime:
                return i        
        # 모든 요소보다 크다면 마지막 인덱스 반환
        return len(예상시간List) - 1
    
    def _get_운영가동률( obj:dict ) -> float:
        """ 운영가동률 계산 """
        if obj.get('plan_qty') == 0 or obj.get('plan_qty') is None:
            return 0
        return float("{:.1f}".format(obj.get('job_qty') / obj.get('plan_qty') * 100))

    생산계획실적_list = fetch_생산계획()    
    휴식시간_list = fetch_휴식시간()
    sensor_별_휴식시간_list = get_sensor별_휴식시간list( 휴식시간_list ) ### { 'sensor_01': [ (datetime.time(10, 30), datetime.time(10, 40)), ..] }
    # print ( sensor_별_휴식시간_list )
    sensor_기준정보_dict = get_sensor_기준정보()
    ### 예상 생산시간 계산 
    예상생산_time = get_예상생산_time(생산계획실적_list, sensor_기준정보_dict, sensor_별_휴식시간_list)



    for _dict in 생산계획실적_list:
        _dict['생산capa'] = len(예상생산_time[_dict['sensor_id']])
        _dict['달성률'] =  _get_달성률( _dict )
        _dict['운영tt'] = _get_운영tt( _dict )
        _dict['이론생산량'] = _get_이론생산량( 예상생산_time[_dict['sensor_id']], datetime.now().time() )
        _dict['운영가동률'] = _get_운영가동률( _dict )
    ### 최대 생산량 계산 _get_달성률
    # 생산계획실적_list = [ get_max_생산량( 생산계획실적_list, get_sensor_기준정보() )
    

    
    log_message = {
        "status": "completed",
        "message": f"생산모니터링 작업 (qs count: {len(생산계획실적_list)} , job_id: {job_id})",
    }

    return {
        "log": log_message,
        "redis_publish": 생산계획실적_list
    }

