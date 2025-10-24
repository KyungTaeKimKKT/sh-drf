import requests, datetime, json,os
from urllib.parse import urlencode, quote_plus, unquote

import logging, traceback
logger = logging.getLogger(__name__)
import time
### 기상청 const
URL_기상청_공공DATA =  "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"


def api_기상청(**kwargs):
	ServiceKey_기상청_공공DATA = os.environ.get('ServiceKey_기상청_공공DATA')
	s = time.perf_counter()
	기상청_API_Results = {}
	nx = nx if(nx:= kwargs.get('nx', False)) else 69
	ny = ny if(ny:= kwargs.get('ny', False)) else 115
		
	objWeather = {}
	url = URL_기상청_공공DATA
	serviceKey = ServiceKey_기상청_공공DATA
	serviceKeyDecoded = unquote(serviceKey, 'UTF-8')

	now = datetime.datetime.now()
	today = datetime.date.today().strftime("%Y%m%d")
	y = datetime.date.today() - datetime.timedelta(days=1)
	yesterday = y.strftime("%Y%m%d") 

	if now.minute<45: # base_time와 base_date 구하는 함수
		if now.hour==0:
			base_time = "2330"
			base_date = yesterday
		else:
			pre_hour = now.hour-1
			if pre_hour<10:
				base_time = "0" + str(pre_hour) + "30"
			else:
				base_time = str(pre_hour) + "30"
			base_date = today
	else:
		if now.hour < 10:
			base_time = "0" + str(now.hour) + "30"
		else:
			base_time = str(now.hour) + "30"
			
	base_date = today


	queryParams = '?' + urlencode({ quote_plus('serviceKey')    : serviceKeyDecoded, 
									quote_plus('pageNo')        :'1',
									quote_plus('numOfRows')     :'100',
									quote_plus('dataType')      : 'json', 
									quote_plus('base_date')     : base_date,
									quote_plus('base_time')     : base_time, 
									quote_plus('nx') : nx, quote_plus('ny') : ny,
									})

	retry_count = 0
	max_retries = 3
	while retry_count < max_retries:
		try:
			response = requests.get(url + queryParams, verify=False)
			items_list:list = response.json().get('response').get('body').get('items').get('item')
			SKY = {
				'1': '맑음',
				'2': '맑음',
				'3': '구름많음',
				'4': ' 흐림',
			}
			PTY = {
				'0':'강수없음',
				'1':'비',
				'2':'비/눈',
				'3':'눈',
				'5':'빗방물',
				'6':'빗방울눈날림',
				'7':'눈날림'
			}

			fcstTimes = list(set([obj['fcstTime'] for obj in items_list]))
			fcstTimes.sort()		#### fcstTimes = ['0900','1000','1100','1200','1300','1400'] 형태임
			
			for fcstTime in fcstTimes:
				objWeather = {}
				filterList = [obj for obj in items_list if obj['fcstTime'] == fcstTime]
				
				
				for obj in filterList:
					objWeather[obj.get('category')] = obj['fcstValue']
				기상청_API_Results[fcstTime] = objWeather
				
			return {
				'log': f"기상청 조회 완료 : {len(기상청_API_Results)} 건 : 소요시간 : {int((time.perf_counter()-s)*1000)} msec",
				'redis_publish': 기상청_API_Results
			}
		
		except Exception as e:
			retry_count += 1
			logger.error(f"기상청 조회 실패 (시도 {retry_count}/{max_retries}) : {e}")
			logger.error(traceback.format_exc())
			if retry_count >= max_retries:
				return {
					'log': f"기상청 조회 실패 : {traceback.format_exc()}",
					'redis_publish': None
				}



def main_job(job_id:int):
	return api_기상청()

def getBaseTime():
	now = datetime.datetime.now()
	after_hour = now.hour+1
	if after_hour<10:
		base_time = "0" + str(after_hour) + "00"
	else:
		base_time = str(after_hour) + "00"
	return base_time

def str_to_time (str):
	# str = '1900'  ==> time  ' 19:00:00'
	time_str = f"{str[0:2]}:{str[2:]}:00"
	return datetime.strptime(time_str, '%H:%M:%S').time()

def str_to_date (str):
	# str = '20220811'  ==> date '2022-08-11'
	date_str = f"{str[0:4]}-{str[4:6]}-{str[6:]}"    
	return datetime.strptime( date_str, "%Y-%m-%d" ).date()



if __name__ == '__main__':
	print ( 'run')
	print(api_기상청())
