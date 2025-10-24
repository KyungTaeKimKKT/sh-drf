"""
Views for 샘플관리 APIs
"""
from drf_spectacular.utils import (
	extend_schema_view,
	extend_schema,
	OpenApiParameter,
	OpenApiTypes,
)

from rest_framework import (
	viewsets,
	mixins,
	status,
)
# from rest_framework.pagination import PageNumberPagination

from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime, date,time, timedelta
from django.http import QueryDict
### https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
from django.forms.models import model_to_dict
from django.db.models import Count, Sum , functions, Q, Max
from util.base_model_viewset import DBViewPermissionMixin, CacheMixin, BaseModelViewSet
from util.base_api_view import BaseAPIView
from django.db import transaction
import util.cache_manager as Cache_Manager
from util.trigger_ws_redis_pub import trigger_ws_redis_pub

import os, time
import json
import copy
import pandas as pd

from .serializers import *
from util.customfilters import *
import util.utils_func as Util
from .customfilters import *
from collections import Counter

import logging, traceback
logger = logging.getLogger(__name__)

from .models import (
	출하현장_master_DB, 
	# 개인별_DB, 
	관리자등록_DB,
	영업mbo_설정DB,
	영업mbo_엑셀등록,
	고객사_DB, 
	구분_DB,
	기여도_DB,
	사용자_DB,
	년간보고_지사_고객사,
	년간보고_지사_구분,
	년간보고_개인별,
	년간보고_달성률_기준 ,
	보고기준_DB,
	신규현장_등록_DB,
	사용자등록_DB,
	Temp_출하현장_master_DB,
)


def str_to_bool(value):
	return str(value).lower() in ('true', '1', 'yes')

def remove_duplicates_출하현장MASTER_DB():
	"""중복 데이터 제거 메소드"""
	try:
		year =2024
		month = 11
		
		# 중복 체크할 필드들
		fields_to_check = ['현장명']#, '고객사', '구분', '담당자', '금액']
		
		# 해당 연월의 데이터 조회
		queryset = 출하현장_master_DB.objects.filter(매출_year=year, 매출_month=month)
		
		# 중복 레코드 찾기
		duplicates = (
			queryset.values(*fields_to_check)
			.annotate(count=Count('id'), max_id=Max('id'))
			.filter(count__gt=1)
		)

		print ('duplicates: ', duplicates.count() )
		for dup in duplicates:
			print ( dup )
		return 
		
		deleted_count = 0
		# 각 중복 그룹에 대해
		for dup in duplicates:
			# 중복 조건 생성
			filter_conditions = {field: dup[field] for field in fields_to_check}
			
			# 해당 조건의 모든 레코드 조회 (최신 ID 제외)
			records_to_delete = (
				queryset.filter(**filter_conditions)
				.exclude(id=dup['max_id'])
			)
			
			deleted_count += records_to_delete.count()
			# 삭제 실행
			records_to_delete.delete()
		

		
	except Exception as e:
		print ( e )

def combine_qs(qs_실적, qs_계획):
	import copy

	month_keys = [f'month_{str(i).zfill(2)}' for i in range(1, 13)]

	def clear_month(data):
		for key in month_keys + ['합계']:
			data[key] = 0
		return data

	def calculate_합계(data):
		data['합계'] = sum(data.get(k, 0) for k in month_keys)
		return data

	def calculate_달성률(계획, 실적):
		달성률 = copy.deepcopy(계획)
		달성률['분류'] = '달성률'
		for key in month_keys:
			계획_val = 계획.get(key, 0)
			실적_val = 실적.get(key, 0)
			달성률[key] = int(실적_val / 계획_val * 100) if 계획_val else 0
		계획_합계 = 계획.get('합계', 0)
		실적_합계 = 실적.get('합계', 0)
		달성률['합계'] = int(실적_합계 / 계획_합계 * 100) if 계획_합계 else 0
		return 달성률

	mapping_month = {i: f'month_{str(i).zfill(2)}' for i in range(1, 13)}
	combined_qs = []

	# 1. 부서별 계획/실적/달성률 (TOTAL 제외)
	for 계획 in [q for q in qs_계획 if q['부서'] != '회사계' and q['구분'].upper() != 'TOTAL']:
		copyed_계획 = copy.deepcopy(계획)
		combined_qs.append(copyed_계획)

		실적_data = clear_month(copy.deepcopy(계획))
		실적_data['분류'] = '실적'

		for 실적 in qs_실적:
			if 실적['부서'] == 계획['부서'] and 실적['구분'] == 계획['구분']:
				월키 = mapping_month.get(실적['매출_month'])
				if 월키:
					실적_data[월키] = 실적.get('총합', 0)

		실적_data = calculate_합계(실적_data)
		combined_qs.append(실적_data)
		combined_qs.append(calculate_달성률(copyed_계획, 실적_data))

	# 2. 부서별 TOTAL (모든 실적 합산)
	for 계획 in [q for q in qs_계획 if q['부서'] != '회사계' and q['구분'].upper() == 'TOTAL']:
		copyed_계획 = copy.deepcopy(계획)
		combined_qs.append(copyed_계획)

		실적_data = clear_month(copy.deepcopy(계획))
		실적_data['분류'] = '실적'

		for row in [q for q in combined_qs if q['부서'] == 계획['부서'] and q['분류'] == '실적']:
			for key in month_keys:
				실적_data[key] += row.get(key, 0)

		실적_data = calculate_합계(실적_data)
		combined_qs.append(실적_data)
		combined_qs.append(calculate_달성률(copyed_계획, 실적_data))

	# 3. 회사 전체 TOTAL (각 구분별 합산)
	for 계획 in [q for q in qs_계획 if q['부서'].upper() == '회사계']:
		copyed_계획 = copy.deepcopy(계획)
		combined_qs.append(copyed_계획)

		실적_data = clear_month(copy.deepcopy(계획))
		실적_data['분류'] = '실적'

		for row in [q for q in combined_qs if q['부서'] != '회사계' and q['분류'] == '실적' and q['구분'] == 계획['구분']]:
			for key in month_keys:
				실적_data[key] += row.get(key, 0)

		실적_data = calculate_합계(실적_data)
		combined_qs.append(실적_data)
		combined_qs.append(calculate_달성률(copyed_계획, 실적_data))

	## add 비정규
	실적_data = clear_month(copy.deepcopy( qs_계획[0] ) )
	실적_data['부서'] = '비정규'
	실적_data['구분'] = '비정규'
	실적_data['분류'] = '실적'
	실적_data['지사_보고순서'] = 99999999   
	for 실적 in qs_실적:
		if 실적['부서'] == '비정규' and 실적['구분']== '비정규' :
			print ( 실적 )
			월키 = mapping_month.get(실적['매출_month'])
			if 월키:
				실적_data[월키] = 실적.get('총합', 0)


	실적_data = calculate_합계(실적_data)
	combined_qs.append(실적_data)

	return sorted(combined_qs, key=lambda x: x['지사_보고순서'])


def combine_qs_개인별(qs_실적, qs_계획):
	import copy

	month_keys = [f'month_{str(i).zfill(2)}' for i in range(1, 13)]

	def clear_month(data):
		for key in month_keys + ['합계']:
			data[key] = 0
		return data

	def calculate_합계(data):
		data['합계'] = sum(data.get(k, 0) for k in month_keys)
		return data

	def calculate_달성률(계획, 실적):
		달성률 = copy.deepcopy(계획)
		달성률['분류'] = '달성률'
		for key in month_keys:
			계획_val = 계획.get(key, 0)
			실적_val = 실적.get(key, 0)
			달성률[key] = int(실적_val / 계획_val * 100) if 계획_val else 0
		계획_합계 = 계획.get('합계', 0)
		실적_합계 = 실적.get('합계', 0)
		달성률['합계'] = int(실적_합계 / 계획_합계 * 100) if 계획_합계 else 0
		return 달성률

	mapping_month = {i: f'month_{str(i).zfill(2)}' for i in range(1, 13)}
	combined_qs = []

	# 1. 개인별 계획/실적/달성률 (TOTAL 제외)
	for 계획 in qs_계획:
		copyed_계획 = copy.deepcopy(계획)
		combined_qs.append(copyed_계획)

		실적_data = clear_month(copy.deepcopy(계획))
		실적_data['분류'] = '실적'

		for 실적 in qs_실적:
			if 실적['부서'] == 계획['부서'] and 실적['담당자'] == 계획['담당자']:
				월키 = mapping_month.get(실적['매출_month'])
				if 월키:
					실적_data[월키] = 실적.get('총합', 0)

		실적_data = calculate_합계(실적_data)
		combined_qs.append(실적_data)
		combined_qs.append(calculate_달성률(copyed_계획, 실적_data))
	
	return combined_qs




class 영업MBO_보고서_개인별_ApiView(BaseAPIView):
	APP_ID = 161
	use_cache: bool = False

	def handle_get(self, request, format=None):
		start_time = time.time()
		response_data = self.get_data(request, format)
		end_time = time.time()
		print ( f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
		return response_data

	def get_data(self, request, format=None):
		매출_year = request.query_params.get('매출_year', 2024)
		base_filter = {'매출_year':매출_year}

		values_filter = ['매출_year', '매출_month'] +['부서','담당자']
		
		mapping_month = {i: f'month_{str(i).zfill(2)}' for i in range(1, 13)}
		month_keys = [f'month_{str(i).zfill(2)}' for i in range(1, 13)]

		postsql_qs_계획 = ( 년간보고_개인별.objects.filter(매출년도=매출_year, 분류='계획')
				.values( '매출년도', '부서', '담당자', '분류', 'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06', 'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12','합계','개인_보고순서')
				.order_by('개인_보고순서')
		)

		postsql_qs_실적 = ( 출하현장_master_DB.objects.filter(**base_filter)
				.values( *values_filter )
				.annotate( 총합 = Sum('금액') )
				.order_by('매출_month')
				)
		response_data = combine_qs_개인별( postsql_qs_실적, postsql_qs_계획 )

		return response_data





class 영업MBO_보고서_지사_고객사_ApiView(BaseAPIView):
	APP_ID = 159
	use_cache: bool = False

	def handle_get(self, request, format=None):
		start_time = time.time()
		response_data = self.get_data(request, format)
		end_time = time.time()
		print ( f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
		return response_data
	
	def get_data(self, request, format=None):
		url_params = request.query_params
		start_time = time.time()
		매출_year = request.query_params.get('매출_year', 2024)
		base_filter = {'매출_year':매출_year}
		values_filter = ['매출_year', '매출_month'] +['부서','고객사']
		
		mapping_month = {i: f'month_{str(i).zfill(2)}' for i in range(1, 13)}
		month_keys = [f'month_{str(i).zfill(2)}' for i in range(1, 13)]

		postsql_qs_실적 = ( 출하현장_master_DB.objects.filter(**base_filter)
				.values( *values_filter )
				.annotate( 총합 = Sum('금액') )
				.order_by('매출_month')
				)
		calcurated_data = []

		for 실적 in postsql_qs_실적:
			실적_data = {'매출년도':매출_year,						  
						  '부서':실적['부서'],
						  '고객사':실적['고객사'],
						  '분류':'실적',
			  }
			월키 = mapping_month.get(실적['매출_month'])
			if 월키:
				실적_data[월키] = 실적.get('총합', 0)
			calcurated_data.append(실적_data)


		# 데이터를 병합할 dict (key: tuple, value: dict)
		merged = {}

		for row in calcurated_data:
			# 고유 키: 매출년도, 부서, 고객사, 분류
			key = (row['매출년도'], row['부서'], row['고객사'], row['분류'])

			# 기존 데이터 가져오거나 초기화
			if key not in merged:
				merged[key] = {
					'매출년도': row['매출년도'],
					'부서': row['부서'],
					'고객사': row['고객사'],
					'분류': row['분류'],
					**{k: 0 for k in month_keys},  # 월은 0으로 초기화
				}

			# 현재 row의 월 데이터만 merged에 더함
			for mk in month_keys:
				if mk in row:
					merged[key][mk] += row[mk]

		# 합계 계산
		for item in merged.values():
			item['합계'] = sum(item[mk] for mk in month_keys)

		# 리스트로 변환
		result = list(merged.values())
		# 👉 전체 합계 행 만들기
		total_row = {
			'매출년도': 매출_year,
			'부서': '전체',
			'고객사': '전체',
			'분류': '합계',
		}

		# 각 월별 합계 계산
		for mk in month_keys:
			total_row[mk] = sum(item[mk] for item in result)

		# 전체 합계
		total_row['합계'] = sum(total_row[mk] for mk in month_keys)
		# 리스트 맨 앞에 삽입
		result.insert(0, total_row)
		order_keys = { '부서': ['전체','경기','중부','남부','비정규'],
						'고객사':['전체','현대','OTIS','TKE', '기타'],
		}
		def sort_key(row):
			dept = row.get('부서', '')
			client = row.get('고객사', '')
			dept_index = next((i for i, d in enumerate(order_keys['부서']) if d in dept), len(order_keys['부서']))
			client_index = next((i for i, c in enumerate(order_keys['고객사']) if c in client), len(order_keys['고객사']))
			return (dept_index, client_index)

		# result 리스트 정렬 (단, 첫 번째는 전체 합계이므로 제외하고 정렬)
		result[1:] = sorted(result[1:], key=sort_key)
		return result


class 영업MBO_보고서_ApiViewSet ( BaseAPIView ):
	APP_ID = 160
	
	def handle_get(self, request, format=None):
		start_time = time.time()
		response_data = self.get_data(request, format)
		end_time = time.time()
		print ( f"DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
		return response_data



	def get_data(self, request, format=None):
		url_params = request.query_params
		start_time = time.time()
		매출_year = request.query_params.get('매출_year', 2024)
		매출_month = request.query_params.get('매출_month', '')
		고객사 = request.query_params.get('고객사', '')
		구분 = request.query_params.get('구분', '')
		부서 = request.query_params.get('부서', '')
		담당자 = request.query_params.get('담당자', '')
		print ( 매출_year, 매출_month, 고객사, 구분, 부서, 담당자 )
		base_filter = {}

		if 매출_year:
			base_filter['매출_year'] = 매출_year
		if 매출_month:
			base_filter['매출_month'] = 매출_month
		if 고객사:
			base_filter['고객사'] = 고객사			
		if 구분:
			base_filter['구분'] = 구분			
		if 부서:
			base_filter['부서'] = 부서			
		if 담당자:
			base_filter['담당자'] = 담당자			
		
		print ( base_filter )

		values_filter = ['매출_year', '매출_month'] +['부서','구분']
		
		postsql_qs_실적 = ( 출하현장_master_DB.objects.filter(**base_filter)
				.values( *values_filter )
				.annotate( 총합 = Sum('금액') )
				.order_by('매출_month')
				)
		
		postsql_qs_계획 = ( 년간보고_지사_구분.objects.filter(매출년도=매출_year, 분류='계획')
				.values('매출년도', '부서', '구분','분류', 'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06', 'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12','합계','지사_보고순서')
				.order_by('부서')
				)

		response_data = combine_qs(postsql_qs_실적, postsql_qs_계획)

		### add 비정규	


		end_time = time.time()
		print ( f"{url_params} DB 조회 시간: {int((end_time - start_time) * 1000)} msec" )
		return response_data
		# return Response(response_data)


class 출하현장_master_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 출하현장_master_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 출하현장_master_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['현장명']
	filterset_class =  출하현장_master_DB_Filter


	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 신규현장_등록_DB_ViewSet(viewsets.ModelViewSet):
	""" 사용자 등록"""
	MODEL = 신규현장_등록_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 신규현장_등록_DB_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['현장명']

	# def list(self, request, *args, **kwargs):
	# 	queryset = self.filter_queryset(self.get_queryset())
	# 	serializer = self.get_serializer(queryset, many=True)
	# 	return Response(serializer.data)

	def get_queryset(self):
		return self.MODEL.objects.order_by('id')
		# q = Q( sales_input_fks__등록자= self.request.user )  | Q( sales_input_fks = None ) 
		# print ( self, type(self.request.user), self.request.user )
		return  self.MODEL.objects.filter( q ).order_by('-id').distinct()
	
	def get_serializer_context(self):
		"""
			Extra context provided to the serializer class.
		"""
		return {
			'request': self.request,
			'format': self.format_kwarg,
			'view': self,
			'user' : self.request.user,

		}
	
class 신규현장_등록_DB_관리자용_ViewSet(viewsets.ModelViewSet):
	"""  관리자 등록"""
	MODEL = 신규현장_등록_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 신규현장_등록_DB_관리자용_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =['현장명']

	def get_queryset(self):
		# print ( self, type(self.request.user), self.request.user )
		return  self.MODEL.objects.order_by('-id')
	



class 사용자마감_View(APIView):

	def post(self, request, format=None):

		query = { key : int(value) for key, value in request.data.items() }

		QS = 신규현장_등록_DB.objects.filter ( ** query ).all()
		for _instance in QS:
			_instance.admin_input_fk = None
			_instance.save()
		
		QS = 신규현장_등록_DB.objects.filter ( ** query ).all()
		QS_2이상 = QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks__gte=2 )
		QS_only1 =  QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks = 1 )
		QS_None =  QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks = 0 )
		summary = {
			'2이상' :QS_2이상.count(),
			'only1' : QS_only1.count(),
			'None' : QS_None.count(),
		}

		for _instance in QS_only1:
			for fk in _instance.sales_input_fks.all():
				_instance.admin_input_fk = fk
				_instance.save()
		# for _inst in 사용자등록_DB.objects.filter ( ** query ).all():

		return Response ( {'result' : summary })


class 년간목표생성_View(APIView):

	def post(self, request, format=None):
		print ( self, request.data )
		매출년도 = request.data['year']
		if (is_조직:=request.data['is_조직'] ) and is_조직 == 'True':
			### 신규 생성 : db 지우고 다시
			if ( is_조직_new := request.data['is_조직_new'] ) and is_조직_new == 'True':
				년간보고_지사_구분.objects.filter( 매출년도=매출년도).delete()

				MBO_표시명_부서 = set(list( User.objects.all().values_list('MBO_표시명_부서', flat=True)))
				MBO_표시명_부서 = ['회사계'] + [ 부서 for 부서 in MBO_표시명_부서 if 부서]
				for 부서 in MBO_표시명_부서:
					if 부서 == '비정규':
						년간보고_지사_구분.objects.create( 매출년도=매출년도,부서=부서,구분=구분,분류='실적' )
					else:	
						for 구분 in set(list(구분_DB.objects.all().values_list('구분_id', flat=True))):
							if 구분 == '비정규' : continue
							for 분류 in ['계획','실적','달성률']:
								data = {'매출년도':int(매출년도), '부서':부서, '구분':구분, '분류':분류 }								
								print ( data )
								data['지사_보고순서'] = 10000
								년간보고_지사_구분.objects.create( **data )

			elif ( is_조직_new := request.data['is_조직_new'] ) and is_조직_new == 'False':
				MBO_표시명_부서 = set(list( User.objects.all().values_list('MBO_표시명_부서', flat=True)))
				MBO_표시명_부서 = ['회사계'] + [ 부서 for 부서 in MBO_표시명_부서 if 부서]
				for 부서 in MBO_표시명_부서:
					if 부서 == '비정규':
						년간보고_지사_구분.objects.create( 매출년도=매출년도,부서=부서,구분=구분,분류='실적' )
					else:	
						for 구분 in set(list(구분_DB.objects.all().values_list('구분_id', flat=True))):
							if 구분 == '비정규' : continue
							for 분류 in ['계획','실적','달성률']:
								data = {'매출년도':int(매출년도), '부서':부서, '구분':구분, '분류':분류 }
								data['지사_보고순서'] = 10000
								print ( data )
								년간보고_지사_구분.objects.get_or_create( **data )

		if (is_개인:=request.data['is_개인'] ) and is_개인 == 'True':
			### 신규 생성 : db 지우고 다시
			QS = User.objects.exclude( MBO_표시명_부서='비정규').annotate( text_len=functions.Length('MBO_표시명_부서')).filter( text_len__gt=2)
			if ( is_개인_new := request.data['is_개인_new'] ) and is_개인_new == 'True':
				년간보고_개인별.objects.filter( 매출년도=매출년도).delete()

			for user in QS:
				if user.user_성명 == '비정규' : continue
				for 분류 in ['계획','실적','달성률']:
					data = {'매출년도':int(매출년도), '부서':user.MBO_표시명_부서, '담당자':user.user_성명, '분류':분류 }
					data['개인_보고순서'] = 10000
					print ( data )
					년간보고_개인별.objects.get_or_create( **data )

		return Response(status=status.HTTP_200_OK, data={'result':True})


		QS = 신규현장_등록_DB.objects.filter ( ** query ).all()
		for _instance in QS:
			_instance.admin_input_fk = None
			_instance.save()
		
		QS = 신규현장_등록_DB.objects.filter ( ** query ).all()
		QS_2이상 = QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks__gte=2 )
		QS_only1 =  QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks = 1 )
		QS_None =  QS.annotate(num_sales_input_fks=Count('sales_input_fks')).filter(num_sales_input_fks = 0 )
		summary = {
			'2이상' :QS_2이상.count(),
			'only1' : QS_only1.count(),
			'None' : QS_None.count(),
		}

		for _instance in QS_only1:
			for fk in _instance.sales_input_fks.all():
				_instance.admin_input_fk = fk
				_instance.save()
		# for _inst in 사용자등록_DB.objects.filter ( ** query ).all():

		return Response ( {'result' : summary })

class 관리자마감_View(APIView):

	def post(self, request, format=None):
		if ( is_관리자마감 := request.data.get('is_관리자마감', False) ) and is_관리자마감 == 'True':

			query:dict = json.loads ( request.data.get('query') )

			설정DB_instance = 영업mbo_설정DB.objects.get( **query )
			설정DB_instance.is_관리자마감 = True
			설정DB_instance.save()

			QS = 신규현장_등록_DB.objects.filter ( ** query ).all()			
			
			_writeDict = {}
			for _instance in QS:
				for name in ['매출_month','매출_year','현장명', '금액','id_made']:
					_writeDict[name] = getattr( _instance, name )
				for name in ['고객사','구분','기여도','비고',]:
					_writeDict[name] = getattr ( _instance.admin_input_fk, name)
				_writeDict['check_admin'] = _instance.admin_input_fk.by_admin
				_writeDict['부서'] = _instance.admin_input_fk.등록자.MBO_표시명_부서
				_writeDict['담당자'] = _instance.admin_input_fk.등록자.user_성명
				출하현장_master_DB.objects.create(** _writeDict )

				_instance.is_관리자마감 = True
				_instance.save()
			
			return Response ( {'result' : 'ok' })
		return Response ( {'result' : '' })




class  사용자등록_DB_ViewSet(BaseModelViewSet):
	MODEL = 사용자등록_DB 
	APP_ID = 157
	use_cache = False
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 사용자등록_DB_Serializer

	ordering_fields = ['신규현장_fk__현장명']
	ordering = ['신규현장_fk__현장명']

	def get_queryset(self):
		return  self.MODEL.objects.filter(등록자=self.request.user)
	
	def perform_create(self, serializer):
		serializer.save( 등록자=self.request.user, 등록자_snapshot=self.request.user.user_성명 )
	
	def get_filtered_list(self):
		acitve_설정 = get_active_설정()
		# 전체 기준 현장 목록
		기준현장들 = 신규현장_등록_DB.objects.filter(설정_fk=acitve_설정).order_by('현장명')
		사용자입력 = { u.신규현장_fk_id: u for u in self.get_queryset() }

		results = []
		for idx, 현장 in enumerate(기준현장들):
			사용자_데이터 = 사용자입력.get(현장.id)
			if 사용자_데이터:
				사용자_dict = 사용자등록_DB_Serializer(사용자_데이터).data
			else:
				빈사용자 = 사용자등록_DB(신규현장_fk=현장)  # 또는 id만 설정도 가능
				사용자_dict = 사용자등록_DB_Serializer(빈사용자).data
				사용자_dict['id'] = -idx		#### 빈 데이터 일때 id 값을 -1로 설정

			results.append({
				**신규현장_등록_DB_Serializer(현장).data,
				**사용자_dict
			})
		return results
	
	def list(self, request, *args, **kwargs):
		results = self.get_filtered_list()
		return Response(results)
	
	@action(detail=False, methods=['post'], url_path='bulk')
	def bulk(self, request, *args, **kwargs):
		datas = json.loads(request.data.get('datas') )
		if isinstance(datas, list):
			with transaction.atomic():	
				for data in datas:
					serializer = self.get_serializer(data=data)
					serializer.is_valid(raise_exception=True)
					serializer.save()
		return Response(status=status.HTTP_200_OK, data=self.get_filtered_list())
	
	@action (detail=False, methods=['post'], url_path='batch_post')
	def batch_post(self, request, *args, **kwargs):
		try:
			print ( request.data )
			print ( request.data.get('datas') )
			datas = json.loads(request.data.get('datas'))
			print ( '받은 data수 : ', len(datas) , isinstance(datas, list) )
			with transaction.atomic():
				cratedNo, updatedNo, deletedNo = 0, 0, 0
				for data in datas:
					id = data['id']
					if id is not None and id > 0:
						instance = self.get_queryset().get(pk=id)
						is_delete = not data['is_선택']   # 선택 해제 시 삭제
						if is_delete:
							instance.delete()
							deletedNo += 1
							continue
						serializer = self.get_serializer(instance=instance, data=data)
						updatedNo += 1
					else:
						serializer = self.get_serializer(data=data)
						cratedNo += 1
					serializer.is_valid(raise_exception=True)
					_instance = serializer.save()
					print ( '생성된 객체:', _instance.pk )
				print ( '생성수 : ', cratedNo, '수정수 : ', updatedNo, '삭제수 : ', deletedNo )
			print ( 'return data:', self.get_filtered_list() )
			return Response(status=status.HTTP_200_OK, data=self.get_filtered_list())
		except Exception as e:
			logger.error(f"Error in batch_post: {e}")
			logger.error(f"Error in batch_post: {traceback.format_exc()}")
			return Response(status=status.HTTP_400_BAD_REQUEST, data=str(e))

	@action(detail=False, methods=['get'], url_path='default-user-input')
	def default_user_input(self, request, *args, **kwargs):
		latest_entry = (
			출하현장_master_DB.objects
			.filter(담당자=request.user.user_성명)
			.order_by('-id')  # 최신 입력 기준
			.values('매출_year', '매출_month')
			.first()
		)

		if not latest_entry:
			return Response( {'고객사':'현대EL','구분':'MOD','기여도':'3'}, status=status.HTTP_200_OK)

		year = latest_entry['매출_year']
		month = latest_entry['매출_month']

		qs = 출하현장_master_DB.objects.filter(
			담당자=request.user.user_성명,
			매출_year=year,
			매출_month=month
		).values('고객사', '구분', '기여도')

		if not qs.exists():
			return Response({"detail": "해당 월에 입력된 기록이 없습니다."}, status=status.HTTP_204_NO_CONTENT)

		def most_common(field):
			return Counter([item[field] for item in qs if item[field]]).most_common(1)[0][0]

		try:
			result = {
				'고객사': most_common('고객사') if most_common('고객사') else '현대EL',
				'구분': most_common('구분') if most_common('구분') else 'MOD',
				'기여도': most_common('기여도') if most_common('기여도') else '3',
			}
			return Response(result, status=status.HTTP_200_OK)
		except Exception:
			return Response({"detail": "기본값 추출 중 오류 발생"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class 사용자등록_DB_ViewSet(viewsets.ModelViewSet):
# 	MODEL = 영업mbo_엑셀등록
# 	queryset = MODEL.objects.order_by('-id')
# 	serializer_class = 영업mbo_엑셀등록_Serializer
# 	# search_fields =['serial'] 
# 	# filterset_class =  Serial_DB_FilterSet

# 	def get_queryset(self):
# 		try:
# 			_instanceRunning =  영업mbo_설정DB.objects.filter( is_검증=True, is_시작=True,is_완료=True).latest( 'id' )
# 		except:
# 			return []

# 		query = { name :getattr(_instanceRunning, name )  for name in ['매출_year', '매출_month'] }
# 		return  self.MODEL.objects.filter(**query).order_by('-id')
	

class 관리자등록_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 관리자등록_DB 
	APP_ID = 158
	use_cache = False
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 관리자등록_DB_Serializer

	ordering_fields = ['신규현장_fk__현장명']
	ordering = ['신규현장_fk__현장명']


	def get_queryset(self):
		return  self.MODEL.objects.select_related('담당자_fk').all()
	
	def get_filtered_list(self):
		acitve_설정 = get_active_설정()
		# 전체 기준 현장 목록
		기준현장들 = 신규현장_등록_DB.objects.filter(설정_fk=acitve_설정).order_by('현장명')
		# 관리자 입력 데이터
		qs_관리자등록 = self.get_queryset().filter(신규현장_fk__설정_fk=acitve_설정)
		관리자입력 = { u.신규현장_fk_id: u for u in qs_관리자등록 }

		# 관리자등록_DB 기준으로 사용자등록수 계산
		사용자등록수_map = (
			qs_관리자등록
			.values('신규현장_fk')
			.annotate(등록수=Count('id'))
		)
		사용자등록수_dict = {item['신규현장_fk']: item['등록수'] for item in 사용자등록수_map}
		print (사용자등록수_dict)

		results = []
		for idx, 현장 in enumerate(기준현장들):
			해당_관리자들 = qs_관리자등록.filter(신규현장_fk=현장)

			if 해당_관리자들.exists():
				for 관리자 in 해당_관리자들:
					관리자_dict = 관리자등록_DB_Serializer(관리자).data
					results.append({
						**신규현장_등록_DB_Serializer(현장, include_금액=True).data,
						**관리자_dict,
						'사용자등록수': 사용자등록수_dict.get(현장.id, 0),
					})
			else:
				빈관리자 = 관리자등록_DB(신규현장_fk=현장)
				관리자_dict = 관리자등록_DB_Serializer(빈관리자).data
				append_dict = {
					**신규현장_등록_DB_Serializer(현장, include_금액=True).data,
					**관리자_dict,
					'사용자등록수': 0,
				}
				#### 여기에 id 값을 추가
				append_dict['id'] = -idx
				append_dict['is_선택'] = True
				results.append(append_dict)
		logger.info(results)
		return results
	
	def list(self, request, *args, **kwargs):
		results = self.get_filtered_list()
		return Response(results)
	
	def get_copyList_to_master_DB(self, active_설정, request):
		master_bulk = []
		now = timezone.now()
		부서_dict = { u.id : u.MBO_표시명_부서 for u in User.objects.filter(MBO_표시명_부서__isnull=False) }
		부서_dict_byName = { u.user_성명 : u.MBO_표시명_부서 for u in User.objects.filter(MBO_표시명_부서__isnull=False) }

		# 1. Temp DB 기준으로 변환

		temp_qs = Temp_출하현장_master_DB.objects.filter(설정_fk=active_설정 )
		for temp in temp_qs:
			구분 = temp.구분
			부서 = '비정규' if 구분 == '비정규' else 부서_dict_byName.get(temp.담당자, '')
			담당자 = '비정규' if 구분 == '비정규' else temp.담당자
			master_bulk.append(출하현장_master_DB(
				매출_month=active_설정.매출_month,
				매출_year=active_설정.매출_year,
				현장명=temp.현장명,
				고객사=temp.고객사,
				구분=구분,
				부서=부서,
				담당자=담당자,
				기여도=temp.기여도,
				비고=temp.비고,
				check_admin=temp.check_admin,
				금액=temp.금액,
				id_made=temp.id_made,
				등록자=request.user.user_성명,
				등록일 = now,
				# 등록_weekno=temp.등록_weekno,
				설정_fk = active_설정,
			))

		# 2. 관리자등록_DB 기준으로 변환
		admin_qs = 관리자등록_DB.objects.filter(신규현장_fk__설정_fk=active_설정)
		for admin in admin_qs:
			구분 = admin.구분
			부서 = '비정규' if 구분 == '비정규' else 부서_dict.get(admin.담당자_fk_id, '')
			담당자 = '비정규' if 구분 == '비정규' else (admin.담당자_fk.user_성명 if admin.담당자_fk else '')
			master_bulk.append(출하현장_master_DB(
				매출_month=active_설정.매출_month,
				매출_year=active_설정.매출_year,
				현장명=admin.신규현장_fk.현장명 if admin.신규현장_fk else '',
				고객사=admin.고객사,
				구분=구분,
				부서=부서,
				담당자=담당자,
				기여도=admin.기여도,
				비고=admin.비고,
				check_admin=admin.check_admin,
				금액 = admin.신규현장_fk.금액 if admin.신규현장_fk else 0,
				등록자=request.user.user_성명,
				등록일 = now,
				설정_fk = active_설정,
			))
		return master_bulk

	@action(detail=False, methods=['get'], url_path='request-to-close-admin-input')
	def request_to_admin_close(self, request, *args, **kwargs):
		active_설정 = get_active_설정()
		bulk_list = self.get_copyList_to_master_DB(active_설정, request)
		logger.info(f"bulk_list: {len(bulk_list)}")

		if bulk_list:
			with transaction.atomic():
				active_설정.is_완료 = True
				active_설정.save()
				출하현장_master_DB.objects.bulk_create(bulk_list)

			return Response(status=status.HTTP_200_OK, data={'result':'ok'})
		else:
			return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'no data'})


	@action(detail=False, methods=['get'], url_path='request-to-sum-user-input')
	def request_to_sum_user_input(self, request, *args, **kwargs):
		""" 사용자 입력 마감. 
			사용자 입력 데이터를 복사시, 'is_선택' 된 것으로 복사
		"""
		try:
			acitve_설정 = get_active_설정()
			기준현장들 = 신규현장_등록_DB.objects.filter(설정_fk=acitve_설정)
			qs_사용자등록 = 사용자등록_DB.objects.filter(신규현장_fk__in=기준현장들)

			to_create = []
			for 사용자 in qs_사용자등록:
				to_create.append(관리자등록_DB(
					신규현장_fk=사용자.신규현장_fk,
					담당자_fk=사용자.등록자,
					고객사=사용자.고객사,
					구분=사용자.구분,
					담당자=사용자.등록자_snapshot,
					기여도=사용자.기여도,
					비고=사용자.비고,
					등록자=request.user.user_성명,
					is_선택=사용자.is_선택,
				))

			with transaction.atomic():
				### 기입력된 clear				
				관리자등록_DB.objects.filter(신규현장_fk__in=기준현장들).delete()
				관리자등록_DB.objects.bulk_create(to_create)

			return Response(status=status.HTTP_200_OK, data= self.get_filtered_list())
		except Exception as e:
			logger.exception("request_to_sum_user_input failed")
			return Response(status=500, data={'error': str(e)})


	@action (detail=False, methods=['post'], url_path='batch_post')
	def batch_post(self, request, *args, **kwargs):
		try:
			print ( request.data )
			print ( request.data.get('datas') )
			datas = json.loads(request.data.get('datas'))
			print ( '받은 data수 : ', len(datas) , isinstance(datas, list) )
			with transaction.atomic():
				cratedCnt, updatedCnt, deletedCnt = 0, 0, 0
				for data in datas:
					id = data['id']
					data['등록자'] = request.user.user_성명
					if id is not None and id > 0:
						instance = self.get_queryset().get(pk=id)
						is_delete = not data['is_선택']   # 선택 해제 시 삭제
						if is_delete:
							instance.delete()
							deletedCnt += 1
							continue
						serializer = self.get_serializer(instance=instance, data=data)
						updatedCnt += 1
					else:
						serializer = self.get_serializer(data=data)
						cratedCnt += 1
					serializer.is_valid(raise_exception=True)
					_instance = serializer.save()
					print ( '생성된 객체:', _instance.pk )
				print ( '생성수 : ', cratedCnt, '수정수 : ', updatedCnt, '삭제수 : ', deletedCnt )
			print ( 'return data:', self.get_filtered_list() )
			return Response(status=status.HTTP_200_OK, data=self.get_filtered_list())
		except Exception as e:
			logger.error(f"Error in batch_post: {e}")
			logger.error(f"Error in batch_post: {traceback.format_exc()}")
			return Response(status=status.HTTP_400_BAD_REQUEST, data=str(e))
	
	@action(detail=False, methods=['post'], url_path='bulk')
	def bulk(self, request, *args, **kwargs):
		try:
			datas = json.loads(request.data.get('datas', '[]'))
			logger.info(datas)

			if not isinstance(datas, list):
				return Response(status=400, data={'error': 'Invalid data format (must be list)'})

			bulk_create_list = []
			bulk_update_list = []
			fields = []
			selected_row_ids = set()
			for _dict in datas:
				_id = _dict.get('id')
				# 외래키 처리: 신규현장_fk 필드를 ID에서 객체로 변환
				신규현장_fk_id = _dict.get('신규현장_fk')
				담당자_fk_id = _dict.get('담당자_fk')
				if 신규현장_fk_id:
					try:
						_dict['신규현장_fk'] = 신규현장_등록_DB.objects.get(id=신규현장_fk_id)
						_dict['담당자_fk'] = User.objects.get(id=담당자_fk_id)
					except 신규현장_등록_DB.DoesNotExist:
						logger.error(f"신규현장_등록_DB with id {신규현장_fk_id} does not exist.")
						continue

				if _id is None or _id == '' or  int(_id) < 1:
					_dict.pop('id')
					bulk_create_list.append(self.MODEL(**_dict))
				else:
					if not fields:
						fields = list(_dict.keys())
						fields = [f for f in _dict.keys() if f != 'id']
					bulk_update_list.append(self.MODEL(**_dict))
					selected_row_ids.add(int(_id))

			with transaction.atomic():
				if bulk_create_list:
					self.MODEL.objects.bulk_create(bulk_create_list)
					# selected_row_ids.update([obj.id for obj in bulk_create_list])  # Ensure new IDs are included
				if bulk_update_list:
					self.MODEL.objects.bulk_update(bulk_update_list, fields)

				logger.info(f"선택된_fk_id_set: {selected_row_ids}")
				if selected_row_ids:
					self.delete_unselected_rows(selected_row_ids)

			return Response(status=status.HTTP_200_OK, data=self.get_filtered_list())

		except Exception as e:
			logger.exception("Bulk save failed")
			return Response(status=500, data={'error': str(e)})	

	def delete_unselected_rows(self, selected_row_ids: set):
		active_설정 = get_active_설정()

		# 전체 중복된 신규현장_fk 찾기
		중복_fk_qs = (
			self.MODEL.objects
			.filter(신규현장_fk__설정_fk=active_설정)
			.values('신규현장_fk')
			.annotate(count=Count('id'))
			.filter(count__gt=1)
		)
		중복_fk_ids = [item['신규현장_fk'] for item in 중복_fk_qs]
		logger.info(f"중복_fk_ids: {중복_fk_ids}")

		# 중복된 것 중 선택되지 않은 개별 row만 삭제
		삭제_qs = (
			self.MODEL.objects
			.filter(신규현장_fk__in=중복_fk_ids)
			.exclude(id__in=selected_row_ids)
		)
		logger.info(f"삭제 대상: {삭제_qs}")
		삭제_qs.delete()


class 영업mbo_설정DB_ViewSet( BaseModelViewSet ):
	MODEL: type[영업mbo_설정DB] = 영업mbo_설정DB
	APP_ID = 156
	use_cache = False
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 영업mbo_설정DB_Serializer
	search_fields =['매출_year','매출_month'] 
	ordering_fields = ['매출_year','매출_month']
	ordering = ['-매출_year','-매출_month']

	def get_queryset(self):
		return super().get_queryset()
		# remove_duplicates_출하현장MASTER_DB()

	def 분석_현장명_존재여부_및_통계(self,given_data: list[dict]):
		# 모델에서 존재하는 현장명 집합
		model_site_names = set(
			출하현장_master_DB.objects.values_list("현장명", flat=True)
		)

		포함 = []
		미포함 = []

		for entry in given_data:
			현장명 = entry.get("현장명")
			금액 = entry.get("금액", 0)
			if 현장명 in model_site_names:
				포함.append((현장명, 금액))
			else:
				미포함.append((현장명, 금액))

		# 통계 계산
		def 통계계산(목록):
			return {
				"개수": len(목록),
				"금액합계": sum(금액 for _, 금액 in 목록)
			}

		포함_통계 = 통계계산(포함)
		미포함_통계 = 통계계산(미포함)

		# 최종 검증
		전체_개수 = len(given_data)
		전체_금액 = sum(entry.get("금액", 0) for entry in given_data)

		검증 = {
			"총개수검증": 전체_개수 == 포함_통계["개수"] + 미포함_통계["개수"],
			"총금액검증": 전체_금액 == 포함_통계["금액합계"] + 미포함_통계["금액합계"],
		}

		return {
			"포함_통계": 포함_통계,
			"미포함_통계": 미포함_통계,
			"검증": 검증,
			"포함_목록": 포함,
			"미포함_목록": 미포함,
		}
	
	@action(detail=False, methods=['get'], url_path='template')
	def template(self, request, *args, **kwargs):
		data = self.get_template_data()
		latest_instance = self.MODEL.objects.order_by(
			'-매출_year',  # 내림차순
			'-매출_month', 
			'-id'           # 동일 월이면 최근 id
		).first()
		if latest_instance:
        	# 최신 매출년도/월
			latest_year = latest_instance.매출_year
			latest_month = latest_instance.매출_month

			# 다음 달 계산
			if latest_month == 12:
				next_year = latest_year + 1
				next_month = 1
			else:
				next_year = latest_year
				next_month = latest_month + 1
			# data 업데이트
			data['매출_year'] = next_year
			data['매출_month'] = next_month
		return Response(status=status.HTTP_200_OK, data=data)
	
	@action(detail=False, methods=['post'], url_path='bulk_create')
	def bulk_create(self, request, *args, **kwargs):
		def parse_data(data: QueryDict) -> dict:
			_dict = {}
			for k in data:
				if k == 'file':
					_dict[k] = data.get(k)
				else:
					val = data.get(k)
					if val in ['True', 'False']:
						val = val == 'True'
					elif val.isdigit():
						val = int(val)
					_dict[k] = val
			return _dict
		
		def get_포함목록_bulk_list(포함목록:list[tuple[str,int]], 설정_fk:영업mbo_설정DB) -> list[Temp_출하현장_master_DB]:				# 1. with 밖에서 먼저 포함 목록의 템플릿 리스트 구성 (단, 설정_fk 없이)
			포함_bulk_list = []
			포함_현장명들 = [현장명 for (현장명, _) in 포함목록]
			latest_instances = (
				출하현장_master_DB.objects
				.filter(현장명__in=포함_현장명들)
				.order_by('현장명', '-id')
			)

			latest_map = {}
			for instance in latest_instances:
				if instance.현장명 not in latest_map:
					latest_map[instance.현장명] = instance

			for (현장명, 금액) in result['포함_목록']:
				latest = latest_map.get(현장명)
				if latest:
					new_obj = {
						field.name: getattr(latest, field.name)
						for field in latest._meta.fields
						if field.name != 'id'
					}

					# ✅ 엑셀 데이터 기준으로 덮어쓰기
					new_obj['매출_year'] = 설정_fk.매출_year
					new_obj['매출_month'] = 설정_fk.매출_month
					new_obj['금액'] = 금액
					new_obj['설정_fk'] = 설정_fk
					포함_bulk_list.append(Temp_출하현장_master_DB(**new_obj))
			return 포함_bulk_list


		def validate_data_and_update(_dict:dict, result:dict) -> None|dict:
			if result['검증']['총개수검증'] and result['검증']['총금액검증']:
				_dict['모든현장_count'] = result['포함_통계']['개수']+result['미포함_통계']['개수']
				_dict['모든현장_금액_sum'] = result['포함_통계']['금액합계']+result['미포함_통계']['금액합계']
				_dict['신규현장_count'] = result['미포함_통계']['개수']
				_dict['신규현장_금액_sum'] = result['미포함_통계']['금액합계']
				_dict['기존현장_count'] = result['포함_통계']['개수']
				_dict['기존현장_금액_sum'] = result['포함_통계']['금액합계']
				_dict['is_시작'] = False
				_dict['is_완료'] = False
				_dict['is_검증'] = True
				_dict['id_made'] = str(_dict['매출_year'])+'-'+str(_dict['매출_month'])
				return _dict
			else:
				return None

		data = request.data.copy()
		excel_datas:list[dict] = json.loads(data.get('excel_datas', '[]')) 
		data.pop('excel_datas')
		_dict = parse_data(data)
		result = self.분석_현장명_존재여부_및_통계(given_data=excel_datas)
		_dict = validate_data_and_update(_dict, result)
		if _dict:
			with transaction.atomic():
				### 1. 설정 인스턴스 생성
				_instance = self.MODEL.objects.create(**_dict)

				### 2. 포함 목록 생성
				포함_bulk_list = get_포함목록_bulk_list(result['포함_목록'], _instance)
				if 포함_bulk_list:
					Temp_출하현장_master_DB.objects.bulk_create(포함_bulk_list)

				### 3. 미포함 목록 생성
				미포함_bulk_list = [
					신규현장_등록_DB(현장명=현장명, 금액=금액, 설정_fk=_instance, 매출_month=_instance.매출_month, 매출_year=_instance.매출_year)
					for (현장명, 금액) in result['미포함_목록']
				]
				if 미포함_bulk_list:
					신규현장_등록_DB.objects.bulk_create(미포함_bulk_list)

			_instance.refresh_from_db()
			serializer = self.get_serializer(_instance)
			return Response(status=status.HTTP_200_OK, data=serializer.data)

		return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'검증 실패'})

	@action(detail=True, methods=['patch','put'], url_path='update_진행현황')
	def update_진행현황(self, request, *args, **kwargs):
		data = request.data.copy()
		_instance = self.get_object()
		serializer = self.get_serializer(_instance, data=data, partial=True)
		if serializer.is_valid():
			is_시작 = serializer.validated_data.get('is_시작', False)
			is_완료 = serializer.validated_data.get('is_완료', False)
			if is_시작:
				with transaction.atomic():
					serializer.save()
					self.app권한_db_update(is_Run= True )
			if is_완료:
				with transaction.atomic():
					serializer.save()
					self.app권한_db_update(is_Run=False)
			if any([is_시작, is_완료]):
				trigger_ws_redis_pub(handle_name='app_권한')
			serializer.instance.refresh_from_db()
			return Response(status=status.HTTP_200_OK, data=serializer.data)
		return Response(status=status.HTTP_400_BAD_REQUEST, data={'error':serializer.errors})


	def app권한_db_update(self, is_Run:bool=True) -> None:
		qs = Api_App권한.objects.filter(div='영업mbo', name__in =['사용자등록','관리자등록'])
		for obj in qs:
			obj.is_Run = is_Run
			obj.save()

	def create(self, request, *args, **kwargs):
		s_time = time.perf_counter()
		logger.info ( request.data )
		file = request.data.get('file')
		if file:
			import pandas as pd
			df = pd.read_excel(file)

			logger.info(df)
			_dictList = df.to_dict(orient='records')
			copyedDict = copy.deepcopy(_dictList[0])
			for key in ['현장명','금액','id_made']:
				del copyedDict[key]

			result = self.분석_현장명_존재여부_및_통계(given_data=_dictList)
			if result['검증']['총개수검증'] and result['검증']['총금액검증']:
				copyedDict['모든현장_count'] = result['포함_통계']['개수']+result['미포함_통계']['개수']
				copyedDict['모든현장_금액_sum'] = result['포함_통계']['금액합계']+result['미포함_통계']['금액합계']
				copyedDict['신규현장_count'] = result['미포함_통계']['개수']
				copyedDict['신규현장_금액_sum'] = result['미포함_통계']['금액합계']
				copyedDict['기존현장_count'] = result['포함_통계']['개수']
				copyedDict['기존현장_금액_sum'] = result['포함_통계']['금액합계']
				copyedDict['is_시작'] = False
				copyedDict['is_완료'] = False
				copyedDict['is_검증'] = True
				copyedDict['id_made'] = str(copyedDict['매출_year'])+'-'+str(copyedDict['매출_month'])
				### file 추가
				copyedDict['file'] = file

				# 1. with 밖에서 먼저 포함 목록의 템플릿 리스트 구성 (단, 설정_fk 없이)
				포함_bulk_list = []
				포함_현장명들 = [현장명 for (현장명, _) in result['포함_목록']]
				latest_instances = (
					출하현장_master_DB.objects
					.filter(현장명__in=포함_현장명들)
					.order_by('현장명', '-id')
				)

				latest_map = {}
				for instance in latest_instances:
					if instance.현장명 not in latest_map:
						latest_map[instance.현장명] = instance

				for (현장명, 금액) in result['포함_목록']:
					latest = latest_map.get(현장명)
					if latest:
						new_obj = {
							field.name: getattr(latest, field.name)
							for field in latest._meta.fields
							if field.name != 'id'
						}

						# ✅ 엑셀 데이터 기준으로 덮어쓰기
						new_obj['매출_year'] = _dictList[0].get('매출_year')
						new_obj['매출_month'] = _dictList[0].get('매출_month')
						new_obj['금액'] = 금액
						포함_bulk_list.append(Temp_출하현장_master_DB(**new_obj))

				# 2. with 안에서 설정 인스턴스 생성 후 설정_fk만 주입하여 bulk_create
				with transaction.atomic():
					_instance = self.MODEL.objects.create(**copyedDict)

					# 설정_fk 주입
					for obj in 포함_bulk_list:
						obj.설정_fk = _instance

					if 포함_bulk_list:
						Temp_출하현장_master_DB.objects.bulk_create(포함_bulk_list)

					# 미포함 bulk list 구성 및 생성
					미포함_bulk_list = [
						신규현장_등록_DB(현장명=현장명, 금액=금액, 설정_fk=_instance, 매출_month=_instance.매출_month, 매출_year=_instance.매출_year)
						for (현장명, 금액) in result['미포함_목록']
					]
					if 미포함_bulk_list:
						신규현장_등록_DB.objects.bulk_create(미포함_bulk_list)


				logger.info(f"result: {result}")

				# 안전하게 serializer 직전 갱신
				_instance.refresh_from_db()
				serializer = self.get_serializer(_instance)
				logger.info(f"serializer: {serializer.data}")
				logger.info(f"time: {(time.perf_counter() - s_time)*1000:.2f} msec")
				return Response(status=status.HTTP_200_OK, data=serializer.data)
			
		return Response(status=status.HTTP_400_BAD_REQUEST, data={'result':'검증 실패'})


	def update(self, request, *args, **kwargs):
		logger.info(request.data)

		_instance: 영업mbo_설정DB = self.get_object()
		is_시작 = str_to_bool(request.data.get('is_시작', False))
		is_완료 = str_to_bool(request.data.get('is_완료', False))

		if is_시작 and not _instance.is_시작:
			logger.info(f'is_시작: {is_시작}  _instance.is_시작: {_instance.is_시작}')
			with transaction.atomic():
				_instance.is_시작 = True
				_instance.save()
				self.app권한_db_update(is_Run=True)
				trigger_ws_redis_pub(handle_name='app_권한')

		if is_완료 and not _instance.is_완료:
			logger.info(f'is_완료: {is_완료}  _instance.is_완료: {_instance.is_완료}')
			with transaction.atomic():
				_instance.is_완료 = True
				_instance.save()
				self.app권한_db_update(is_Run=False)
				trigger_ws_redis_pub(handle_name='app_권한')
		_instance.refresh_from_db()
		serializer = self.get_serializer(_instance)
		return Response(status=status.HTTP_200_OK, data=serializer.data)


	def destroy(self, request, *args, **kwargs):
		try:
			instance = self.get_object()
			#### db 초기화
			query = { key: getattr(instance, key) for key in ['매출_year', '매출_month']}

			출하현장_master_DB.objects.filter(**query).delete()
			신규현장_등록_DB.objects.filter(**query).delete()
			if instance.file:
				if os.path.isfile(instance.file.path):
					os.remove(instance.file.path)
			self.perform_destroy(instance)
		except :
			pass
		return Response(status=status.HTTP_204_NO_CONTENT)
	
	def db_update_보고용_all(self, _instance:영업mbo_설정DB ) -> None:
		query = { key:getattr(_instance, key) for key in ['매출_year','매출_month']}
		df = pd.DataFrame( list(출하현장_master_DB.objects.filter( **query ).values() ))
	
		# 금액s = [ _inst.금액  for _inst in 출하현장_master_DB.objects.filter( **query ) ]
		# print ( 'query: ', query, 'sum(금액s): ', sum(금액s) )
		# print ( df )
		# print ( df['금액'].sum() )
		# print ( df['금액'].sum() == sum(금액s) )

		## 😀 db update
		self._db적용_지사_구분( _instance, df )
		self._db적용_지사_고객사( _instance, df )
		self._db적용_개인별 (_instance, df )
		
	
	def _db적용_지사_구분(self, _instance:영업mbo_설정DB, df:pd.DataFrame ) -> None:
		df_pivot = df.pivot_table( index=['부서','구분'], aggfunc='sum', values='금액')
		d = df_pivot.reset_index()
		results:list[dict] = d.to_dict( orient='records')

		name_month =  f"month_{str(_instance.매출_month).zfill(2)}"

		QS = 년간보고_지사_구분.objects.filter( 매출년도=_instance.매출_year )
		### 구분 : NE, MOD등 실적
		for obj in results:
			query = {  '부서' : obj.get('부서'), '구분' : obj.get('구분'), '분류':'실적' }
			try:
				_inst, created = QS.exclude(부서='회사계').get_or_create(**query)
				setattr(_inst, name_month, obj.get('금액'))
				_inst.save()
			except  Exception as e:
				logger.error(f" 년간보고_지사_구분 : {e}")
				logger.error(f" 년간보고_지사_구분 : {traceback.format_exc()}")
		### 구분 : TOTAL 실적
		QS = 년간보고_지사_구분.objects.filter( 매출년도=_instance.매출_year )
		query = {  '구분':'TOTAL',  '분류':'실적'  }
		for _inst in QS.exclude(부서='회사계').filter(**query):
			setattr ( _inst, name_month,  sum( [ obj.get('금액') for obj in results if obj.get('부서') == _inst.부서 ]) )
			_inst.save()

		### 분류 : 달성률 실적
		QS = 년간보고_지사_구분.objects.filter( 매출년도=_instance.매출_year )
		query = {  '분류':'달성률'  }
		for _inst in QS.exclude(부서='회사계').filter(**query):
			try:
				_query = { key:getattr(_inst, key) for key in ['매출년도', '부서','구분']}
				계획value = getattr ( QS.get( 분류='계획', **_query ), name_month )

				# 계획value = getattr ( QS.get( 매출년도=_inst.매출년도, 부서=_inst.부서, 구분=_inst.구분, 분류='계획'), name_month )
				실적value = getattr ( QS.get( 분류='실적', **_query ), name_month )
				달성률 = int(실적value / 계획value * 100 ) if 계획value else 0
				setattr ( _inst, name_month, 달성률 )
				_inst.save()
			except Exception as e:
				logger.error(f" 년간보고_지사_구분 : {e}")
				logger.error(f" 년간보고_지사_구분 : {traceback.format_exc()}")

		### 회사계 적용: ## 실적  :  구분 : ['MOD','NE', 'TOTAL']
		QS = 년간보고_지사_구분.objects.filter( 매출년도=_instance.매출_year )
		query = {  '분류':'실적'  }
		for name in ['MOD','NE', 'TOTAL']:
			_inst = QS.filter(부서='회사계',구분=name).get(**query)
			if name == 'TOTAL':
				value = QS.exclude(부서='회사계').filter( 구분__in=['TOTAL','비정규'], **query).aggregate( Sum( name_month ))[f"{name_month}__sum"]
			else:
				value = QS.exclude(부서='회사계').filter( 구분=name, **query).aggregate( Sum( name_month ))[f"{name_month}__sum"]
			setattr ( _inst, name_month, value )
			_inst.save()



		QS = 년간보고_지사_구분.objects.filter( 매출년도=_instance.매출_year )
		query = {  '분류':'달성률'  }
		for name in ['MOD','NE', 'TOTAL']:
			_inst = QS.get(분류='달성률',부서='회사계',구분=name,매출년도= _instance.매출_year )
			계획value = getattr ( QS.get( 부서='회사계', 구분=name, 분류='계획',매출년도= _instance.매출_year ), name_month )
			실적value = getattr ( QS.get( 부서='회사계', 구분=name, 분류='실적',매출년도= _instance.매출_year ), name_month )
			달성률 = int(실적value / 계획value * 100 ) if 계획value else 0

			setattr ( _inst, name_month, 달성률 )
			logger.info(f" 년간보고_지사_구분 : {name} {_inst}  , ... 계획value : {계획value} 실적value : {실적value} 달성률 : {달성률} ")
			_inst.save()


	def _db적용_지사_고객사(self, _instance:영업mbo_설정DB, df:pd.DataFrame ) -> None:

		df_pivot = df.pivot_table( index=['부서','고객사'], aggfunc='sum', values='금액')
		d = df_pivot.reset_index()
		results:list[dict] = d.to_dict( orient='records')

		name_month =  f"month_{str(_instance.매출_month).zfill(2)}"

		QS = 년간보고_지사_고객사.objects.filter( 매출년도=_instance.매출_year )
		### 구분 : NE, MOD등 실적
		for obj in results:
			query = {  '부서' : obj.get('부서'), '고객사' : obj.get('고객사'), '분류':'실적' }
			try:
				_inst, created = QS.exclude(부서='회사계').get_or_create(**query)
				setattr(_inst, name_month, obj.get('금액'))
				_inst.save()
			except  Exception as e:
				logger.error(f" 년간보고_지사_고객사 : {e}")
				logger.error(f" 년간보고_지사_고객사 : {traceback.format_exc()}")


	def _db적용_개인별 (self, _instance:영업mbo_설정DB, df:pd.DataFrame ) -> None:
		df_pivot = df.pivot_table( index=['부서','담당자'], aggfunc='sum', values='금액')
		d = df_pivot.reset_index()
		results:list[dict] = d.to_dict( orient='records')

		name_month =  f"month_{str(_instance.매출_month).zfill(2)}"

		QS = 년간보고_개인별.objects.filter( 매출년도=_instance.매출_year )
		### 구분 : NE, MOD등 실적
		for obj in results:
			query = {  '부서' : obj.get('부서'), '담당자' : obj.get('담당자'), '분류':'실적' }
			try:
				_inst, created = QS.exclude(부서='회사계').get_or_create(**query)
				setattr(_inst, name_month, obj.get('금액'))
				_inst.save()
			except  Exception as e:
				logger.error(f" 년간보고_개인별 : {e}")
				logger.error(f" 년간보고_개인별 : {traceback.format_exc()}")

		### 분류 : 달성률 실적
		QS = 년간보고_개인별.objects.filter( 매출년도=_instance.매출_year )
		query = {  '분류':'달성률'  }
		for _inst in QS.exclude(부서='회사계').filter(**query):
			try:
				_query = { key:getattr(_inst, key) for key in ['매출년도', '부서','담당자']}
				계획value = getattr ( QS.get( 분류='계획', **_query ), name_month )

				# 계획value = getattr ( QS.get( 매출년도=_inst.매출년도, 부서=_inst.부서, 구분=_inst.구분, 분류='계획'), name_month )
				실적value = getattr ( QS.get( 분류='실적', **_query ), name_month )
				달성률 = int(실적value / 계획value * 100 ) if 계획value else 0
				setattr ( _inst, name_month, 달성률 )
				_inst.save()
			except Exception as e:
				logger.error(f" 년간보고_개인별 : {e}")
				logger.error(f" 년간보고_개인별 : {traceback.format_exc()}")


	def _검증(self, request, *args, **kwargs ) ->dict:
		검증_dict = {}
		_instance : 영업mbo_설정DB = kwargs.get('_instance', None)
		if _instance is None : return

		df = pd.read_excel(_instance.file) # can also index sheet by name or fetch all sheets
		# print ( self, '\n\n', df )
		총현장list : list[dict] = df.to_dict(orient='records')
		# print ( self, '\n\n', 총현장list )
		검증_dict['모든현장_count'] = len(총현장list)
		검증_dict['모든현장_금액_sum'] = int( sum ( [ obj.get('금액',0) for obj in 총현장list ] ) )

		# print ( [ obj.get('현장명') for obj in 총현장list ] )
		masterDB_QS = 출하현장_master_DB.objects.filter(현장명__in =[ obj.get('현장명') for obj in 총현장list ] )

		s = time.time()
		기등록현장list = []
		신규현장list = []
		for obj in 총현장list:
			if 출하현장_master_DB.objects.filter(현장명= obj.get('현장명') ).count() >0 :
				기등록현장list.append( obj)
			else :
				신규현장list.append ( obj )

		검증_dict['기존현장_count'] = len(기등록현장list)
		검증_dict['신규현장_count'] = len ( 신규현장list )
		검증_dict['기존현장_금액_sum'] = int (sum ( [ obj.get('금액',0) for obj in 기등록현장list ] ) )
		검증_dict['신규현장_금액_sum'] = int ( sum ( [ obj.get('금액',0) for obj in 신규현장list ] ) )

		검증_dict['등록현장_수_검증'] = bool ( len(총현장list) == len(기등록현장list) +  len ( 신규현장list ) )
		검증_dict['등록현장_금액_검증'] = bool ( 검증_dict['모든현장_금액_sum']  == 검증_dict['기존현장_금액_sum']  +  검증_dict['신규현장_금액_sum'] )

		print ( self, 검증_dict )
		print ( self, '총소요시간:', time.time() - s )
		return  검증_dict

		# mylist = df['column name'].tolist()
		

	def _master적용(self, request, *args, **kwargs ):
		_instance : 영업mbo_설정DB = kwargs.get('_instance', None)
		if _instance is None : return
		df = pd.read_excel(_instance.file) # can also index sheet by name or fetch all sheets
		총현장list : list[dict] = df.to_dict(orient='records')
		for obj in 총현장list:
			if (QS := 출하현장_master_DB.objects.filter(현장명= obj.get('현장명') ).order_by('-id')).count() >0 :
				copyedObj = copy.deepcopy(obj)
				_latestInstance =  QS[0]
				for name in ['고객사','구분','부서','담당자','기여도','등록자'] :
					copyedObj[name] = getattr(_latestInstance, name)
				_created = 출하현장_master_DB.objects.create( **copyedObj  )
			else :
				### 신규 현장 list만 저장함 ... 24-11월 부터
				신규현장_등록_DB.objects.create(**obj)

	@action(detail=False, methods=['get'], url_path='get-매출년도list' )#, permission_classes=[AllowAny], authentication_classes=[])
	def get_매출년도list(self, request, *args, **kwargs):
		print ( self, 'get_매출년도list')
		logger.info(f"[get_매출년도list] user: {request.user}, auth: {request.auth}")
		start_time = time.time()
		_list =  Cache_Manager.get_mbo_매출년도_캐시( key= request.get_full_path() )
		print ( self, '총소요시간:', int((time.time() - start_time) *1000 ) , 'msec')


		return Response( _list )


class 영업MBO_매출년도_API_View(APIView):
	def get(self, request, *args, **kwargs):
		from 영업mbo.models import 영업mbo_설정DB
		_list = list(
					영업mbo_설정DB.objects.order_by('-매출_year')
					.values_list('매출_year', flat=True)
					.distinct()
				)
		return Response( _list )
			
	
class 영업mbo_엑셀등록_ViewSet(viewsets.ModelViewSet):
	MODEL = 영업mbo_엑셀등록
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 영업mbo_엑셀등록_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
class 고객사_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 고객사_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 고객사_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 구분_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 구분_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 구분_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 기여도_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 기여도_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 기여도_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 사용자_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 사용자_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 사용자_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class DB_Field_년간보고_지사_고객사(APIView):
	""" DB FILED VIEW {NAME:TYPE}"""
	MODEL = 년간보고_지사_고객사

	authentication_classes = []
	permission_classes = []

	def get(self, request, format=None):
		return Response ( Util.get_MODEL_field_type(self.MODEL) )
	

class 년간보고_지사_고객사_ViewSet(viewsets.ModelViewSet):
	MODEL = 년간보고_지사_고객사
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 년간보고_지사_고객사_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# authentication_classes = []
	# permission_classes = [IS_Admin_Permission]
	filterset_class = 영업mbo_년간보고_지사_고객사_FilterSet

	authentication_classes = []
	permission_classes = []

	def get_queryset(self):
		return  self.MODEL.objects.order_by('지사_보고순서')
	

class 년간보고_지사_구분_ViewSet(viewsets.ModelViewSet):
	MODEL = 년간보고_지사_구분
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 년간보고_지사_구분_Serializer
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	# authentication_classes = []
	# permission_classes = [IS_Admin_Permission]
	filterset_class = 영업mbo_년간보고_지사_구분_FilterSet

	authentication_classes = []
	permission_classes = []

	def get_queryset(self):
		return  self.MODEL.objects.order_by('지사_보고순서','id')
	
class 년간보고_개인별_ViewSet(viewsets.ModelViewSet):
	MODEL = 년간보고_개인별
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 년간보고_개인별_Serializer
	filter_backends = [
		SearchFilter, 
		filters.DjangoFilterBackend,
	]
	filterset_class = 영업mbo_년간보고_개인별_FilterSet

	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('개인_보고순서','id')


class 년간보고_달성률_기준_ViewSet(viewsets.ModelViewSet):
	MODEL = 년간보고_달성률_기준
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 년간보고_달성률_기준_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	

class 보고기준_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = 보고기준_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = 보고기준_DB_Serializer
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	authentication_classes = []
	permission_classes = []
	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
