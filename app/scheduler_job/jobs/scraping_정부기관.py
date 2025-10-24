from bs4 import BeautifulSoup
import concurrent.futures
import requests
from django.db import transaction
from urllib.parse import urlparse
from urllib.request import urlopen
import datetime
import time, json, copy
from dateutil import parser

import scraping.models as ScrapingModel
from util.utils_func import remove_duplicates_from_model

import logging, os, traceback
### 원칙은 __name__이나, 현재 app의 하위 폴더이므로 
# logger = logging.getLogger(__name__)
logger = logging.getLogger('scheduler_job')
print ( f" 로거 설정 : {logger}")
print ('__name__', __name__)


class 정부기관NEWS_Scraping:
	""" 정부기관 뉴스 스크래핑 
		config :  dict :{'url': 'https://www.moel.go.kr/news/enews/report/enewsList.do', 
						'gov_name': '고용노동부', 
						'구분': '보도자료', 
						'suffix_link': 'https://www.moel.go.kr/news/enews/report/'}
		th_db :  dict  : {'제목': '제목', '등록일': '등록일', '작성일': '등록일', 
					'등록일자': '등록일', '날짜': '등록일', 
					'장학생': '제목금지어', '박종선': '제목금지어'}
	"""
	def __init__(self, config:dict={}, th_db:dict={}, db_attributes:list[str]=[]):
		self.gov_name: str = ''
		self.구분: str = ''
		self.url: str = ''
		self.link_suffix: str = ''
		self.db_attributes: list[str] = db_attributes
		self.ths, self.tds, self.results = [], [], []

		self.th_db = th_db
		self.config = config
		for key, value in self.config.items():
			setattr(self, key, value)

		self.link_testResult = False

		self.defaultDict = {
			'정부기관':self.gov_name,
			'구분' : self.구분,
		}
		self.result = {}
		self.log = {}
		self.errorList = []
		self.timeout = 5.0
		self.soup = self.get_soup( self.url )
		self.run()

	def run(self) -> list[dict]:
		if self.soup is not None:
			match self.gov_name:
				# case '한국소방안전원':		
				# 	ul = self.soup.find( 'ul', {'class':'orderlist'})
				# 	lis = ul.find_all('li')
				# 	for (index,li) in enumerate(lis):
				# 		li : BeautifulSoup
				# 		if ( title:= li.find('p', {'class':'title'}) ):
				# 			title_text = title.text.strip().replace( title.find('span').text, "") 
				# 			_isValid, 등록일 = self.check_등록일_검증(등록일 = li.find_all('span')[2].text.strip() )
				# 			if _isValid :
				# 				link = self.link_suffix + self.get_href( a = li.find('a', href=True) )
				# 				updateDict = copy.deepcopy( self.defaultDict )
				# 				updateDict.update(
				# 					{
				# 						'제목':title_text,
				# 						'등록일' : 등록일,
				# 						'링크' : link,
				# 					} 
				# 				)
				# 				self.results.append (updateDict)

				# 				if index == 0:
				# 					self.check_link_test(link)							

				case _:
					self.ths:list[str] = self.get_tableThs()
					result_list = self.get_tableTds()
					self.results = self.validate_result(result_list)

		return self.results

	# 문자열을 datetime 객체로 파싱한 후 date() 메서드로 날짜만 추출
	def parse_to_date(self, date_string:str) -> datetime.date|None:
		try:
			# 문자열을 datetime 객체로 파싱
			dt = parser.parse(date_string)
			# datetime에서 date 객체만 추출
			return dt.date()
		except Exception as e:
			logger.error(f"날짜 파싱 오류: {e}")
			return None
		
	def validate_result(self, result_list:list[dict]) -> list[dict]:
		""" 검증 결과 반환 """

		날짜_str = None
		for _th_str in self.ths:
			match self.th_db.get(_th_str, None):
				case '제목':
					pass
				case '등록일':
					날짜_str = _th_str
				case _:
					pass

		results = []
		for _obj in result_list:
			# 새 딕셔너리를 생성하여 기존 딕셔너리를 복사
			new_obj = copy.deepcopy(self.defaultDict)
			
			for key, value in _obj.items():
				if key in self.db_attributes:
					if key == 날짜_str:
						new_obj['등록일'] = self.parse_to_date(value)
					else:
						new_obj[key] = value
					
			results.append(new_obj)
		return results

	
	def check_link_test(self, link:str) -> bool:
		### 😀 https://stackoverflow.com/questions/56101612/python-requests-http-response-406
		res = requests.get( link, timeout= self.timeout, headers={"User-Agent": "XY"})
		self.link_testResult = res.ok
		if not self.link_testResult:
			self.errorList.append(f"  {link} test Falil : {res.status_code} -- {self.defaultDict['정부기관']} - {self.defaultDict['구분']}")
		return res.ok
	

	def get_soup(self, url) -> BeautifulSoup|None :
		if not url : return None
		try:
			page = urlopen(url, timeout= self.timeout)
			html:str = page.read().decode("utf-8")
			soup = BeautifulSoup(html, features="html.parser")
			return soup
		except Exception as e:
			self.errorList.append(str(e))
			self.log['url'] = self.errorList
			return None
		

	def get_tableThs(self, soup:BeautifulSoup|None=None) ->list[str]:
		""" get table theads """
		if not soup : 
			soup =self.soup
		web상_ths = [ th.text.strip() for th in soup.find_all('th') ]
		db상_ths = []
		for th_name in web상_ths:
			if th_name in self.th_db:
				db상_ths.append( self.th_db[th_name] )
			else:
				db상_ths.append( th_name )

		return db상_ths  
	
	def get_tableTds(self, soup:BeautifulSoup|None=None ) -> list[dict[str, str]]:
		if not soup : soup =self.soup
		result_list =[]
		try:
			table = soup.find('table')
			table_body = table.find('tbody')
			table_trs = table_body.find_all('tr')
			
			for tr in table_trs:
				tds_dict = {}
				for th, td in zip(self.ths, tr.find_all('td')):
					# 모든 공백, 탭, 개행 문자 등을 제거
					cleaned_text = td.text.strip().replace('\r', '').replace('\n', '').replace('\t', '')
					# 연속된 공백을 하나의 공백으로 대체
					cleaned_text = ' '.join(cleaned_text.split())
					tds_dict[th] = cleaned_text
					tds_dict['링크'] = self.get_href( a = tr.find('a', href=True) )
				result_list.append( tds_dict )
			
			return result_list
		except Exception as e:
			self.errorList.append(f" Anayalis Error: {e}")
			return []
		# global scraping_results
		# scraping_results.append({self.url : result })
		# return result
	
	def get_href(self, a:BeautifulSoup|None=None) -> str:
		if a is None : return '#'
		try:
			#### onclick 경우, 
			if a['href'] == '#':
				###  goTo.view('list','13931','134','0402010000'); return false;
				if a['onclick'] is not None and len(a['onclick']) > 5:
					match self.config.get('gov_name').strip() :
						case '한국승강기안전공단':
							link1 = a['onclick'].replace('(', '__').replace(')', '__').split('__')[1]
							link_list = link1.split(',')
							mId = link_list[3].strip("'")
							bIdx = link_list[1].strip("'")
							ptIdx = link_list[2].strip("'")
							return f"mId={mId}&bIdx={bIdx}&ptIdx={ptIdx}"
						
						case '한국소방안전원':
							link1 = a['onclick'].replace('(', '__').replace(')', '__').split('__')[1]
							link_list = link1.split(',')
							postsSeqno = link_list[0].strip("'")
							postsRnum = link_list[1].strip("'")

							return f"&postsSeqno={postsSeqno}&postsRnum={postsRnum}&searchCondition=title&searchKeyword=&pageIndex=1"
						
						case '_':
							return '#'
				else:
					return '#'

			elif ';jsessionid=' in a['href']:
				linkList = a['href'].split(';')
				return linkList[0]+'?'+linkList[1].split('?')[-1]
				조정된link = linkList[1].split('?')
			else:
				#### 대한 산업안전협회 경우 https://www.safety.or.kr/
				#### /safety/bbs/BMSR00207/view.do;jsessionid=E183C56293052018F959EDB82EFBF652?boardId=229015&menuNo=200082&pageIndex=1&searchCondition=&searchKeyword=
				### 에서 ;jsessionid=E183C56293052018F959EDB82EFBF652 삭제함
				
				return a['href'] if bool(a['href'])  else '#'
		except Exception as e:
			self.errorList.append(f"href find error:{e}")
			return '#'

def get_new_articles_from_db_compare( today_results:list[dict] ) -> tuple[int, list[dict]]:
	""" 오늘 스크래핑된 항목과 DB에 있는 항목을 비교하여 tuple ( 신규 항목 반환 , 삭제된 항목 반환 ) """
	today = datetime.datetime.now().date()
	비교대상_key_values = ['정부기관', '구분', '제목', '링크']
	today_db_values = ScrapingModel.NEWS_DB.objects.filter( 등록일 = today ).values(*비교대상_key_values)

	logger.info( f" 오늘 DB에 있는 항목: {len(today_db_values)}개")
	# DB에 없는 신규 항목 찾기
	new_articles, del_articles = [], []
	
	# DB 항목을 비교하기 쉽게 세트로 변환
	db_items_set = set()
	for db_item in today_db_values:
		# 딕셔너리는 해시 불가능하므로 튜플로 변환
		item_tuple = tuple((k, str(v).strip()) for k, v in db_item.items() if k in 비교대상_key_values)
		db_items_set.add(item_tuple)
	
	# 스크래핑 결과에서 DB에 없는 항목 찾기
	for result_item in today_results:
		# 비교를 위해 동일한 형식으로 변환
		item_tuple = tuple((k, str(result_item.get(k, '').strip())) for k in 비교대상_key_values 
					 if not isinstance ( result_item.get(k, ''), (datetime.date, datetime.datetime)))
		
		# DB에 없는 항목이면 신규 항목 리스트에 추가
		if item_tuple not in db_items_set:
			new_articles.append(result_item)
		else:
			del_articles.append(result_item)

	logger.info( f" 신규 항목: {len(new_articles)}개")
	logger.info( f" 삭제 항목: {len(del_articles)}개")

	return new_articles, del_articles


def update_urls ( new_articles:list[dict] , url_prefix_dict:dict ) -> list[dict]:
	""" 신규 article에 대한 url 접속여부 검증 """
	for _obj in new_articles:
		if _obj and _obj.get('정부기관', '') and _obj.get('구분', ''):
			key = _obj.get('정부기관')+'_'+_obj.get('구분')
			prefix = url_prefix_dict.get(key)
			if prefix is None:
				logger.error(f"{_obj.get('정부기관')} - {_obj.get('구분')} : URL 접두사를 찾을 수 없습니다.")
			else:
				_obj['링크'] = prefix + _obj.get('링크')
	return new_articles

def 검증_urls_접속여부( new_articles:list[dict]  ) -> list[dict]:
	""" 신규 article에 대한 url 접속여부 검증 """

	for _obj in new_articles:
		# _obj['접속여부'] = False
		url = _obj.get('링크').strip()
		if url.startswith('http') or url.startswith('https'):
			try:
				# GET 요청으로 변경 (HEAD 요청이 거부되는 사이트가 있음)
				# 헤더 추가 및 User-Agent 개선
				headers = {
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
					"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
					"Connection": "keep-alive"
				}
				
				# HEAD 요청 대신 GET 요청 사용 (일부 사이트는 HEAD 요청을 거부함)
				response = requests.get(url, timeout=5, allow_redirects=True, headers=headers, stream=True)
				
				# 스트림 모드로 요청하고 일부 콘텐츠만 읽어서 검증 (전체 페이지를 다운로드하지 않음)
				response.raw.read(1024)
				response.close()
				
				# 상태 코드가 200대면 성공
				if 200 <= response.status_code < 300:
					# _obj['접속여부'] = True
					logger.info(f"{_obj.get('정부기관')} - {_obj.get('구분')} : URL 접속 성공: {url}")
				else:
					logger.error(f"{_obj.get('정부기관')} - {_obj.get('구분')} : URL 접속 실패 (상태 코드 {response.status_code}): {url}")
					# _obj['접속여부'] = False
					
			except requests.RequestException as e:
				logger.error(f"{_obj.get('정부기관')} - {_obj.get('구분')} : URL 접속 오류: {url} - {str(e)}")
		else:
			logger.error(f"{_obj.get('정부기관')} - {_obj.get('구분')} : URL 검증 실패 (http로 시작하지 않음): {url}")

	return new_articles



def main_job(job_id:int):
	import time
	s = time.time()
	try:
		#### 1. db에서 기본정보 가져옴. : 정부기관_DB, NEWS_Table_Head_DB
		정부기관_DB_QS = ScrapingModel.정부기관_DB.objects.all().values('url', 'gov_name', '구분','suffix_link')
		정부기관_DB_list = [{k: v.strip() if isinstance(v, str) else v for k, v in obj.items()} for obj in 정부기관_DB_QS]
		NEWS_Table_Head_DB_QS = ScrapingModel.NEWS_Table_Head_DB.objects.all().values('제목','등록일','제목금지어')
		# NEWS_Table_Head_DB_list = [{k: v.split(',') if isinstance(v, str) else v for k, v in obj.items()} for obj in NEWS_Table_Head_DB_QS]
		#### reverse dict
		NEWS_Table_Head_DB_dict = {value: key for item in NEWS_Table_Head_DB_QS for key, values in item.items() for value in values.split(',')}

		db_attributes = ['정부기관', '구분', '제목', '등록일', '링크']
		url_prefix_dict = { _obj.get('gov_name')+'_'+_obj.get('구분') : _obj.get('suffix_link') for _obj in 정부기관_DB_list}

		if not 정부기관_DB_list :
			raise ValueError ( "정부기관_DB_list 가 비어있습니다." )
		if not NEWS_Table_Head_DB_dict :
			raise ValueError ( "NEWS_Table_Head_DB_dict 가 비어있습니다." )
		
		threadingTargets = 정부기관_DB_QS

		# https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread
		### 2. 스크래핑 시작
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = [ executor.submit (정부기관NEWS_Scraping, config , NEWS_Table_Head_DB_dict , db_attributes ) 
						for config in threadingTargets ]
		result_Collections = [f.result() for f in futures]
		
		### 3. 스크래핑 완료
		all_results =[]
		for scraping_instance in result_Collections:
			if scraping_instance.results:
				all_results.extend( scraping_instance.results )

		logger.info( f" 스크래핑 완료: {len(all_results)}개")

		### 4. 오늘 스크래핑된 항목 추출

		for _obj in all_results:
			logger.info( { k: v for k, v in _obj.items() if k not in ['링크'] } )
		today = datetime.datetime.now().date()
		today_results = [ result for result in all_results if result.get('등록일') == today ]
		### 5. 링크 업데이트
		today_results = update_urls( today_results , url_prefix_dict )
		logger.info( f" 오늘자 스크래핑된 항목: {len(today_results)}개")
		### 6. 오늘 스크래핑된 항목과 DB에 있는 항목을 비교하여 신규 항목 반환
		new_articles , del_articles = get_new_articles_from_db_compare( today_results )
		logger.info( f" db에 없는 신규 항목: {len(new_articles)}개")
		logger.info( f" db에 있는 삭제 항목: {len(del_articles)}개")
		### 7. 신규 항목 url 검증
	
		logger.info( f'url 검증 시작: {len(new_articles)}개')

		new_articles = 검증_urls_접속여부( new_articles )

		### 8. 검증 완료
		log = {}
		log['오늘 스크래핑된 항목'] = len(today_results)
		log['DB에 이미 있는 항목'] = len(del_articles)
		log['신규 항목'] = len(new_articles)
		logger.info( f'완료 및 db 저장 시작: {log}')

		### 9. 신규 항목 DB에 저장
		if new_articles:
			db_save_list = [ {k: v for k, v in x.items() if k in db_attributes} for x in new_articles ]

			bulk_list = [ ScrapingModel.NEWS_DB(**article) for article in db_save_list]
			with transaction.atomic():
				ScrapingModel.NEWS_DB.objects.bulk_create(bulk_list)

			### 9. delete dubplicate 항목 DB에서 삭제
			duplicate_counts = remove_duplicates_from_model( ScrapingModel.NEWS_DB, db_attributes )
			logger.info( f" 중복 항목 삭제 완료: {duplicate_counts}개")

		logger.info( f" 소요시간 : {time.time()-s} 초")
		return {
				'log' : log,
				'redis_publish' : new_articles,
			}

	except ValueError as e:
		logger.error( 'ValueError :%s', str(e) ,exc_info=True)
		return {
			'log' : {
				'error' : str(e),			
			}
		}
	except Exception as e:
		logger.error( 'Exception :%s', str(e) )
		logger.error ( f" 상세오류 정보: \n{traceback.format_exc()}")
		return {
			'log' : {
				'error' : str(e),			
			}
		}





if __name__ == '__main__':
	return_value = main_job()
	# logger.info( f" 완료 및 db 저장 완료: {return_value}")
# 	# asyncio.run(main() )
# 	ws = WS(Info.URL_WS_정부기관NEWS_STATUS)
# 	ws.run()

# 	main(ws)

# 	# # scheduler = BackgroundScheduler()
# 	scheduler = BlockingScheduler(job_defaults={'max_instances': 3})
# 	scheduler.add_job( main, trigger='cron',hour='6-23', minute='0,30' , args=[ws], id='main' )
# 	scheduler.start()