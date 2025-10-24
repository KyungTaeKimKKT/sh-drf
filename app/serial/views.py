"""
Views for the serial APIs
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
from django.db.models import Q

from . import serializers, models, generator, customfilters
from 생산관리 import models as 생산관리_models
# from . import customfilters

from util.utils_viewset import Util_Model_Viewset
# from util.customfilters import Serial_DB_FilterSet


class SerialDB_ViewSet(viewsets.ModelViewSet):
	MODEL = models.SerialDB
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SerialDB_Serializer
	
	# search_fields =['serial'] 
	# filterset_class =  Serial_DB_FilterSet

	def get_queryset(self):
		return  self.MODEL.objects.order_by('-id')
	
	def create(self, request, *args, **kwargs):
		try:
			print(request.data)
			# 요청 데이터에서 필요한 정보 추출
			공정코드 = request.data.get('공정코드')
			고객사 = request.data.get('고객사')
			ProductionLine_fk = request.data.get('ProductionLine_id')
			확정Branch_id = request.data.get('확정Branch_id')
			# 생산실적_id = request.data.get('생산실적_id', None)  # 생산실적 ID가 필요할 경우
			# if 생산실적_id:
			# 	qs_생산실적 = 생산관리_models.생산실적.objects.filter(id=생산실적_id)
			# else:
			# 	qs_생산실적 = 생산관리_models.생산실적.objects.filter(
			# 		공정상세_fk__확정Branch_fk=확정Branch_id
			# 	)
			
			# 필수 파라미터 검증
			if not all([공정코드, 고객사, ProductionLine_fk,확정Branch_id]):
				return Response(
					{"error": "공정코드, 고객사, ProductionLine_fk, 확정Branch_id는 필수 항목입니다."}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# 확정Branch 조회
			try:
				확정Branch = 생산관리_models.생산계획_확정Branch.objects.get(id=확정Branch_id)
			except 생산관리_models.생산계획_확정Branch.DoesNotExist:
				return Response(
					{"error": "해당 확정Branch를 찾을 수 없습니다."}, 
					status=status.HTTP_404_NOT_FOUND
				)

			# 현재까지 발행된 시리얼 수 확인
			existing_serials_count = self.MODEL.objects.filter(확정Branch_fk=확정Branch_id, ProductionLine_fk=ProductionLine_fk ).count()
			계획수량 = 확정Branch.생산지시_process_fk.수량

			# 계획수량 초과 체크
			if existing_serials_count >= 계획수량:
				return Response(
					{"error": "해당 확정Branch의 계획수량을 초과하여 시리얼을 발행할 수 없습니다."}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# SerialGenerator를 사용하여 시리얼 생성
			serial = generator.SerialGenerator.generate_serial(
				공정코드=공정코드,
				고객사=고객사
			)

			# SerialDB 모델에 저장
			serializer = self.get_serializer(data={
				'serial': serial,
				'확정Branch_fk': 확정Branch_id,
				'ProductionLine_fk': ProductionLine_fk,
			})
			serializer.is_valid(raise_exception=True)
			serializer.save()

			# 생산실적 정보 조회
			response_data = serializer.data

			response_data.update({
						'current_count': existing_serials_count+1,
						'total_count': 계획수량,
						'remaining_count': 계획수량 - existing_serials_count,
			})

			return Response(response_data, status=status.HTTP_201_CREATED)

		except Exception as e:
			return Response(
				{"error": str(e)}, 
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	

class SerialHistory_ViewSet(viewsets.ModelViewSet):
	MODEL = models.SerialHistory
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SerialHistory_Serializer	
	filter_backends = [
		   SearchFilter, 
		   filters.DjangoFilterBackend,
		]
	search_fields =[] 
	filterset_class =  customfilters.Seiral_History_DB_FilterSet

	def get_queryset(self):
		return self.MODEL.objects.order_by('-id')

	def create(self, request, *args, **kwargs):
		try:
			print(request.data)
			# 요청 데이터 가져오기
			serial = request.data.get('serial')
			production_line_fk = request.data.get('ProductionLine_fk')
			스캔유형 = request.data.get('스캔유형')
			
			# 필수 파라미터 검증
			if not all([serial, production_line_fk, 스캔유형]):
				return Response(
					{"error": "serial, ProductionLine_fk, 스캔유형은 필수 항목입니다."}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# SerialDB에서 해당 시리얼 찾기
			serial_obj = models.SerialDB.objects.filter(serial=serial).first()
			if not serial_obj:
				return Response(
					{"error": "존재하지 않는 시리얼 번호입니다."}, 
					status=status.HTTP_404_NOT_FOUND
				)
			
			# 이미 존재하는 기록 확인
			existing_record = self.MODEL.objects.filter(
				serial_fk= serial_obj,
				ProductionLine_fk=production_line_fk,
				스캔유형=스캔유형
			).exists()

			if existing_record:
				return Response(
					{"error": "이미 완료된 바코드입니다."}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# 생산계획 공정상세에서 해당 시리얼의 확정Branch에 대한 설비 정보 확인
			assigned_production_lines = 생산관리_models.생산계획_공정상세.objects.filter(
				확정Branch_fk=serial_obj.확정Branch_fk,
				# ProductionLine_fk=production_line_fk,
				is_active=True
			).values_list('ProductionLine_fk', flat=True).distinct()

			# 스캔된 설비가 배정된 설비 목록에 없는 경우
			if int(production_line_fk) not in assigned_production_lines:
				# 배정된 설비 정보 가져오기
				assigned_lines = 생산관리_models.ProductionLine.objects.filter(
					id__in=assigned_production_lines
				).values_list('name', flat=True)
				
				assigned_lines_str = ', '.join(assigned_lines)
				
				return Response(
					{
						"error": f"올바르지 않은 설비에서 스캔되었습니다. \n 이 제품은 다음 설비에서 작업해야 합니다: {assigned_lines_str}",	
					}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# request.data를 변경 가능한 형태로 복사
			mutable_data = request.data.copy()
			# 요청 데이터에 serial_fk 추가
			mutable_data['serial_fk'] = serial_obj.id

			# 시리얼 히스토리 생성
			serializer = self.get_serializer(data=mutable_data)
			serializer.is_valid(raise_exception=True)
			serializer.save()

			return Response(serializer.data, status=status.HTTP_201_CREATED)

		except Exception as e:
			return Response(
				{"error": str(e)}, 
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
		
	@action(detail=False, methods=['get'], url_path='개별이력조회')
	def get_serial_history(self, request):
		try:
			# 쿼리 파라미터 가져오기
			serial = request.query_params.get('serial')
			include_작업지시서 = request.query_params.get('작업지시서', 'False').lower() == 'true'
			include_생산지시서 = request.query_params.get('생산지시서', 'False').lower() == 'true'
			print(serial, include_생산지시서,include_작업지시서)
			if not serial:
				return Response(
					{"error": "시리얼 번호는 필수 항목입니다."}, 
					status=status.HTTP_400_BAD_REQUEST
				)

			# 기본 쿼리셋 가져오기
			queryset = self.get_queryset().filter(serial_fk__serial=serial).order_by('스캔시간')
			print(queryset)
			# 시리얼 히스토리 데이터 직렬화
			serializer = self.get_serializer(queryset, many=True)
			response_data = {
				'serial_histories': serializer.data
			}

			# SerialDB 객체 가져오기
			serial_obj = models.SerialDB.objects.filter(serial=serial).first()
			if not serial_obj:
				return Response(
					{"error": "존재하지 않는 시리얼 번호입니다."}, 
					status=status.HTTP_404_NOT_FOUND
				)

			# 생산지시서 정보 포함 또는 작업지시서 정보가 필요한 경우
			if include_생산지시서 or include_작업지시서:
				if serial_obj.확정Branch_fk and serial_obj.확정Branch_fk.일정관리_fk:
					생산지시_obj = serial_obj.확정Branch_fk.일정관리_fk.생산지시_fk
					print('생산지시서:', 생산지시_obj)
	
					if include_생산지시서 and 생산지시_obj:
						from 생산지시.serializers import 생산지시_Serializer
						response_data['생산지시서'] = 생산지시_Serializer(생산지시_obj).data
					
					if include_작업지시서 and 생산지시_obj and 생산지시_obj.작업지침_fk:
						from 작업지침.serializers import 작업지침_Serializer
						response_data['작업지시서'] = 작업지침_Serializer(생산지시_obj.작업지침_fk).data


			return Response(response_data, status=status.HTTP_200_OK)

		except Exception as e:
			return Response(
				{"error": str(e)}, 
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)