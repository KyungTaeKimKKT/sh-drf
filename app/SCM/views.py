"""
Views for the  APIs
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
from django.db.models import Q, F
from itertools import groupby
from operator import itemgetter

from django.core.cache import cache



from . import models, serializers
# from . import customfilters

import 생산지시.models as 생산지시Models
from serial.models import SerialHistory  # SerialHistory 모델 import 추가

from util.utils_viewset import Util_Model_Viewset
from util.customfilters import 생산지시_DB_FilterSet



class SCM_제품_ViewSet(viewsets.ModelViewSet):
	MODEL = models.SCM_제품
	queryset = MODEL.objects.order_by('-id')
	serializer_class = serializers.SCM_제품_Serializer

	# cache_key = '생산관리_ProductionLine'  # 캐시 키
	# cache_time = 60*60*12  # 캐시 유지 시간 (초)
	
	def get_queryset(self):   
		return self.MODEL.objects.order_by('-id').select_related(
			'stock_fk', 
			'stock_fk__창고_fk',
			'stock_fk__생산관리_제품완료_fk',
			'stock_fk__생산관리_제품완료_fk__확정Branch_fk',
			'stock_fk__생산관리_제품완료_fk__확정Branch_fk__생산지시_process_fk',

		)
		queryset = cache.get(self.cache_key)
		
		if queryset is None:
			# 캐시에 데이터가 없으면 DB에서 조회하고 캐시에 저장
			queryset = self.MODEL.objects.order_by('구분','name')
			cache.set(self.cache_key, queryset, self.cache_time)
		return queryset


