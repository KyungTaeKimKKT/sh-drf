
import logging,  copy
from datetime import date, datetime, timedelta, time
import os, traceback

logger = logging.getLogger('scheduler_job')


import 생산모니터링.models_외부 as Models_외부 
import 생산모니터링.models as Models_내부
from datetime import date, datetime, timedelta
from django.core.cache import cache

# @shared_task
def main_job(job_id:int):
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
        is_use_cache = False

        if is_use_cache:
            cache_key = '생산계획_목록'
            생산계획_list = cache.get(cache_key)
            if 생산계획_list is None:
                생산계획_list = ( Models_외부.생산계획실적.objects.using('생산모니터링').
                            filter(start_time__contains=date.today() ).order_by('sensor_id')
                            .values() )
                생산계획_list =[{**항목, 'start_time': 항목['start_time'].time(), 'end_time': 항목['end_time'].time()} for 항목 in 생산계획_list]
                cache.set(cache_key, 생산계획_list, timeout=60*60*1)
        else:
            생산계획_list = ( Models_외부.생산계획실적.objects.using('생산모니터링').
                        filter(start_time__contains=date.today() ).order_by('sensor_id')
                        .values() )
            생산계획_list =[{**항목, 'start_time': 항목['start_time'].time(), 'end_time': 항목['end_time'].time()} for 항목 in 생산계획_list]

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
        # logger.debug (f"start_time: {start_time} , job_qty_time: {job_qty_time}")
        # logger.debug ( f" type: {type(start_time)} , {type(job_qty_time)}")
        # logger.debug ( f" job_qty_time < start_time: {job_qty_time < start_time}")


        tt_시작시간:datetime = job_qty_time if ( job_qty_time < start_time) else  job_qty_time

        운영tt = int( (datetime.now() -tt_시작시간).total_seconds() )
        if 운영tt < 0:
            return 0
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
        이론생산량 =  _get_이론생산량( 예상생산_time[_dict['sensor_id']], datetime.now().time() )
        if 이론생산량 == 0: 
            return 0
        return float("{:.1f}".format(obj.get('job_qty') / 이론생산량 * 100))
    

    def get_status( obj:dict, 휴식시간_list:list[dict]) -> str:

        now = datetime.now()
        today = date.today()
        if  not obj.get('plan_qty', False) : return '생산계획없음'  
        start_time = datetime.combine(today, obj.get('start_time'))
        end_time = datetime.combine(today, obj.get('end_time'))
        
        if  start_time  > now: return '준비'
        elif  end_time  < now: return '종료'



        if any ( 휴식시간포함여부 := [ datetime.combine(today, 휴식시간obj.get('휴식시간_시작')) < now  < datetime.combine(today, 휴식시간obj.get('휴식시간_종료')) for 휴식시간obj in 휴식시간_list  ] ):
        # if ( self.휴식시간_queryset.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__lte = now , 휴식시간_종료__gte = now).order_by("휴식시간_시작") ):
            if ( now <= datetime.combine(today ,time(11,30)) ): return '휴식'
            elif ( now <= datetime.combine(today , time(14,00)) ): return '점심'
            elif ( now <= datetime.combine(today , time(17,00)) ): return '휴식'
            else : 
                return '청소_저녁' 

        if obj.get('운영tt')  <=  100 *2 : return '가동중'
        elif obj.get('운영tt')  <= 100 *5 : return '지연'
        else : return '정지'

        
    try:

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
            _dict['status'] = get_status( _dict, 휴식시간_list )
        ### 최대 생산량 계산 _get_달성률
        # 생산계획실적_list = [ get_max_생산량( 생산계획실적_list, get_sensor_기준정보() )
        copy_생산계획실적_list = copy.deepcopy(생산계획실적_list)
        for _dict in copy_생산계획실적_list:
            del _dict['생성시간']
            _dict['job_qty_time'] = _dict['job_qty_time'].strftime('%H:%M')
            _dict['start_time'] = _dict['start_time'].strftime('%H:%M')
            _dict['end_time'] = _dict['end_time'].strftime('%H:%M')

        생산계획실적_list = copy_생산계획실적_list
        
        log_message = {
            "status": "completed",
            "message": f"생산모니터링 작업 (qs count: {len(생산계획실적_list)} , )",
        }

        # logger.info(log_message)
        # logger.info(생산계획실적_list)   

        # 구독자 = publish_redis(생산계획실적_list)
        # logger.info(f"실행시간: {int((time.time() - time_start)*1000)} msec , 구독자수: {구독자} , 생산계획실적_list: {len(생산계획실적_list)} ")  # 소수점 2자리까지 표시
        return {
            "log": log_message,
            "redis_publish": 생산계획실적_list
        }
    except Exception as e:
        logger.error(f"생산실적_실시간_모니터링 작업 실행 중 오류 발생: {e}")
        logger.error(f"traceback: {traceback.format_exc()}")
        return {
            "log": {"error": str(e), "message": "작업 실행 중 오류가 발생했습니다."},
            "redis_publish": None
        }
    
