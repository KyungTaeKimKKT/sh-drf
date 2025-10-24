"""
Views for the contact APIs
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
# from datetime import datetime, date,time, timedelta
import datetime
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
from django.db import transaction
from django.db.models import Q, F
from itertools import groupby
from operator import itemgetter

from django.core.cache import cache

# from .permissions import (
#     개인_리스트_DB_전사_Permission,
#     개인_리스트_DB_개인_Permission,
#     조직_리스트_DB_전사_Permission,
#     조직_리스트_DB_개인_Permission,
#     전기사용량_DB_Permission,
#     휴일등록_DB_Permission
# )
# from . import serializers

from . import models, serializers
# from . import customfilters

import 생산지시.models as 생산지시Models
from serial.models import SerialHistory  # SerialHistory 모델 import 추가

from util.utils_viewset import Util_Model_Viewset
from util.customfilters import 생산지시_DB_FilterSet



class 판금처_DB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.판금처_DB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.판금처_DB_Serializer

	def get_queryset(self):
		return self.MODEL.objects.order_by('판금처')
	

class ProductionLine_ViewSet(viewsets.ModelViewSet):
	MODEL = models.ProductionLine
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.ProductionLine_Serializer

	cache_key = '생산관리_ProductionLine'  # 캐시 키
	cache_time = 60*60*12  # 캐시 유지 시간 (초)
	
	def get_queryset(self):   
		return self.MODEL.objects.order_by('구분','name')

		queryset = cache.get(self.cache_key)
		
		if queryset is None:
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = self.MODEL.objects.order_by('구분','name')
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset


class 생산계획_DDay_ViewSet(viewsets.ModelViewSet):
	MODEL = models.생산계획_DDay
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산계획_DDay_Serializer

	cache_key = '생산관리_생산계획_DDay'  # 캐시 키
	cache_time = 60*60*12  # 캐시 유지 시간 (초)

	def get_queryset(self):     
		queryset = cache.get(self.cache_key)
		
		if queryset is None:
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = self.MODEL.objects.order_by('-id')
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset 


class 생산계획_Schedule_By_Types_ViewSet(viewsets.ModelViewSet):
	MODEL = models.Schedule_By_Types
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산계획_Schedule_By_Types_Serializer
	def get_queryset(self):       
		return self.MODEL.objects.order_by('-id')
	
	def update(self, request, *args, **kwargs):
		return super().update(request, *args, **kwargs)


class 생산계획_일정관리_ViewSet(viewsets.ModelViewSet):
	""" 생산계획관리 view set """    
	MODEL = models.생산계획_일정관리
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산계획_일정관리_Serializer

	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = 생산지시_Pagination

	def get_queryset(self):    
		return self.MODEL.objects.order_by('-id')
		all_계획반영제외 = ~ (Q(is_계획반영_htm = True) & Q ( is_계획반영_jamb = True) )
		return self.MODEL.objects.filter(all_계획반영제외).order_by('-id')
	


class 생산계획_확정_Branch_ViewSet(viewsets.ModelViewSet, 생산지시_DB_FilterSet):
	""" 생산계획_확정_Branch view set """    
	MODEL = models.생산계획_확정Branch
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산계획_확정Branch_Serializer

	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = 생산지시_Pagination

	def get_queryset(self):    
		# all_계획반영제외 = ~ (Q(is_계획반영_htm = True) & Q ( is_계획반영_jamb = True) )
		return self.MODEL.objects.order_by('id')


class 생산계획_공정상세_ViewSet(viewsets.ModelViewSet):
	""" 생산계획_확정_Branch view set """    
	MODEL = models.생산계획_공정상세
	# 기본 queryset은 메타데이터용으로 유지
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산계획_공정상세_Serializer

	# search_fields =['구분', '고객사','현장명','상세내용','비고'] 
	# pagination_class = 생산지시_Pagination

	def get_queryset(self):    
		# all_계획반영제외 = ~ (Q(is_계획반영_htm = True) & Q ( is_계획반영_jamb = True) )
		return self.MODEL.objects.order_by('확정Branch_fk','공정순서').select_related(
						'확정Branch_fk',
						'ProductionLine_fk'
					).prefetch_related(
						'실적_set',
						'변경이력_set'
					)
		
	@action(detail=False, methods=['get'])
	def get_merged_processes(self, request):
		"""동일 확정Branch와 설비별로 공정을 병합하여 반환"""

		def check_all_processes_complete(확정Branch_id):
            # 한 번의 쿼리로 모든 데이터 가져오기
			processes_data = self.MODEL.objects.filter(
				확정Branch_fk=확정Branch_id, is_HI_complete=False
			).select_related(
				'ProductionLine_fk'
			).values(
				'ProductionLine_fk',
				'확정Branch_fk__계획수량'
			).distinct()
			
			# 계획수량 = processes_data[0]['확정Branch_fk__계획수량'] if processes_data else 0
			확정branch_obj = models.생산계획_확정Branch.objects.get( id=확정Branch_id )
			확정branch_serializer = serializers.생산계획_확정Branch_Serializer(확정branch_obj)
			계획수량 = 확정branch_serializer.data['계획수량']
		
			for process in processes_data:
				실적수량 = get_실적수량(확정Branch_id, process['ProductionLine_fk'])				
				if 실적수량 != 계획수량:
					return False
			return True

		def merge_branch_data(확정Branch_id):
				processes = self.MODEL.objects.filter(확정Branch_fk=확정Branch_id).values(
					'ProductionLine_fk__name',
					'공정명',
					'계획일',
					'id',
					'ProductionLine_fk__구분',
				)
				
				merged_data = {
					'설비명': [],
					'공정명': [],
					'계획일': set(),
					'공정구분': [],
					'공정상세_ids': []
				}
				
				for proc in processes:
					print ( 'proc:', proc )
					if proc['ProductionLine_fk__name'] not in merged_data['설비명']:
						merged_data['설비명'].append(proc['ProductionLine_fk__name'])
					if proc['공정명'] not in merged_data['공정명']:
						merged_data['공정명'].append(proc['공정명'])
					merged_data['계획일'].add(proc['계획일'])
					merged_data['공정상세_ids'].append(proc['id'])
					merged_data['공정구분'].append(proc['ProductionLine_fk__구분'])
				return {
					'설비명': ' + '.join(merged_data['설비명']),
					'공정명': ' + '.join(merged_data['공정명']),
					'계획일': min(merged_data['계획일']) if merged_data['계획일'] else None,
					'공정상세_ids': merged_data['공정상세_ids'],
					'공정구분': merged_data['공정구분'][0],
				}

		def get_실적수량(확정Branch_id, ProductionLine_id):
			cache_key = f'실적수량_{확정Branch_id}_{ProductionLine_id}'
			cached_count = cache.get(cache_key)
			if cached_count is None:
				cached_count = SerialHistory.objects.filter(
					serial_fk__확정Branch_fk=확정Branch_id,
					ProductionLine_fk=ProductionLine_id
				).values('serial_fk').distinct().count()
				cache.set(cache_key, cached_count, 60 * 5)  # 5분간 캐시
                
			return cached_count
		
		def batch_get_실적수량(확정Branch_ids, ProductionLine_ids):
			# 여러 확정Branch와 ProductionLine의 실적 수량을 한 번에 가져오기
			cache_keys = {
				(branch_id, line_id): f'실적수량_{branch_id}_{line_id}'
				for branch_id in 확정Branch_ids
				for line_id in ProductionLine_ids
			}
			
			# 캐시에서 일괄 조회
			cached_results = cache.get_many(cache_keys.values())
			
			# 캐시 미스된 항목들에 대해 DB 조회
			missing_pairs = {
				(branch_id, line_id)
				for (branch_id, line_id), cache_key in cache_keys.items()
				if cache_key not in cached_results
			}
			
			if missing_pairs:
				# DB에서 한 번에 조회
				db_results = SerialHistory.objects.filter(
					Q(*[Q(serial_fk__확정Branch_fk=branch_id, ProductionLine_fk=line_id)
						for branch_id, line_id in missing_pairs], _connector=Q.OR)
				).values(
					'serial_fk__확정Branch_fk',
					'ProductionLine_fk'
				).annotate(
					count=Count('serial_fk', distinct=True)
				)
				
				# 캐시 업데이트
				cache_updates = {
					f'실적수량_{result["serial_fk__확정Branch_fk"]}_{result["ProductionLine_fk"]}': result['count']
					for result in db_results
				}
				cache.set_many(cache_updates, 60 * 5)
				
				cached_results.update(cache_updates)
			
			return cached_results

		# Query Parameter로 창고 이동 조건 체크
		check_warehouse_ready = request.query_params.get('warehouse_ready', 'false').lower() == 'true'

		# 1. 필요한 필드들을 가져오고 정렬
		queryset = self.get_queryset().filter(is_HI_complete=False).select_related(
			'확정Branch_fk', 
			'ProductionLine_fk'
		).order_by(
			'확정Branch_fk', 
			'ProductionLine_fk', 
			'계획일',
			'공정순서'
		).values(
			'id',
			'확정Branch_fk',
			'ProductionLine_fk',
			'ProductionLine_fk__구분',
			'ProductionLine_fk__설비',  # 설비 type: base, MT, CCL 등
			'ProductionLine_fk__name',  # 설비 이름
			'계획일',
			'공정명',
			'공정순서',
			'is_active'
		)

		# 2. 병합된 결과를 저장할 리스트
		merged_processes = []

		# 3. 확정Branch와 설비, 계획일로 그룹화
		def grouping_key(item):
			return (
				item['확정Branch_fk'], 
				item['ProductionLine_fk'],
				item['계획일']
			)

		if check_warehouse_ready:
			# 완료된 확정Branch만 필터링
			completed_branches = set()
			current_branch = None
			merged_result = []

			for item in queryset:
				branch_id = item['확정Branch_fk']
				if branch_id not in completed_branches and check_all_processes_complete(branch_id):
					completed_branches.add(branch_id)
			
			# 완료된 확정Branch들에 대해 데이터 병합
			for branch_id in completed_branches:
				merged_data = merge_branch_data(branch_id)
				확정branch_obj = models.생산계획_확정Branch.objects.get(id=branch_id)
				확정branch_serializer = serializers.생산계획_확정Branch_Serializer(확정branch_obj)
				
				result = 확정branch_serializer.data
				result.update(merged_data)
				result['확정Branch_fk'] = branch_id
				result['실적수량'] = get_실적수량(branch_id, queryset[0]['ProductionLine_fk'])
				# result['공정상세_ids'] = [ p['id'] for p in sorted_processes ]
				
				merged_result.append(result)

			merged_processes = merged_result

		else:
		
			# 4. 그룹별로 처리
			for key, group in groupby(queryset, key=grouping_key):
				merged_data = {}
				group_list = list(group)
				if not group_list:
					continue

				# 첫 번째 항목에서 공통 정보 가져오기
				first_item = group_list[0]
				
				# 공정명들을 공정순서대로 정렬하여 결합
				sorted_processes = sorted(group_list, key=itemgetter('공정순서'))
				merged_process_names = ' + '.join(p['공정명'] for p in sorted_processes)
				공정상세_ids = [ p['id'] for p in sorted_processes ]

				확정branch_obj = models.생산계획_확정Branch.objects.get(id=first_item['확정Branch_fk'])
				확정branch_serializer = serializers.생산계획_확정Branch_Serializer(확정branch_obj)
				확정branch_data = 확정branch_serializer.data

				merged_data.update(확정branch_data)

            # 실적수량 계산 추가
			# 실적수량 = SerialHistory.objects.filter(
            #     serial_fk__확정Branch_fk=first_item['확정Branch_fk'],
            #     ProductionLine_fk=first_item['ProductionLine_fk']
            # ).values('serial_fk').distinct().count()


				# 병합된 데이터 생성
				merged_data.update( {
					'id': first_item['id'],  # 그룹의 첫 번째 id 사용
					'is_active': True,
					'확정Branch_fk': first_item['확정Branch_fk'],
					'ProductionLine_fk': first_item['ProductionLine_fk'],
					'공정구분' : first_item['ProductionLine_fk__구분'],
					'설비': first_item['ProductionLine_fk__설비'],
					'설비명': first_item['ProductionLine_fk__name'],
					'계획일': first_item['계획일'],
					'공정명': merged_process_names,
					'공정순서': sorted_processes[0]['공정순서'] , # 첫 번째 공정의 순서 사용,
					'공정상세_ids' : 공정상세_ids,
					'실적수량': get_실적수량(first_item['확정Branch_fk'], first_item['ProductionLine_fk']),
				} ) 
				merged_processes.append(merged_data)
			

        # 페이지네이션 적용
		page = self.paginate_queryset(merged_processes)
		if page is not None:
			return self.get_paginated_response(page)

		return Response(merged_processes)

	@action(detail=False, methods=['get'])
	def get_process_details(self, request):
		"""개별 공정 상세 정보 반환 (기존 방식)"""
		serializer = self.get_serializer(self.queryset, many=True)
		return Response(serializer.data)


class 생산실적_ViewSet(viewsets.ModelViewSet):
	MODEL = models.생산실적
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산실적_Serializer

	def get_queryset(self):    
		return self.MODEL.objects.order_by('-id')


class 생산관리_제품완료_ViewSet(viewsets.ModelViewSet):
	MODEL = models.생산관리_제품완료
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.생산관리_제품완료_Serializer

	def get_queryset(self):    
		return self.MODEL.objects.select_related(
			'확정Branch_fk'
		).order_by('-id')
	
	@transaction.atomic
	def create(self, request, *args, **kwargs):
		print ( 'request.data:', request.data )
		mutate_data = request.data.copy()
		공정상세_ids = mutate_data.pop('공정상세_ids', [])
		
		# 제품완료 레코드 생성
		serializer = self.get_serializer(data=mutate_data)
		serializer.is_valid(raise_exception=True)
		instance = serializer.save()
		
		# 관련 공정상세 완료 처리
		instance.complete_processes(공정상세_ids, 창고_fk=request.data.get('창고_fk', None))
		
		return Response(serializer.data, status=status.HTTP_201_CREATED)