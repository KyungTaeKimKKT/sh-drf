"""
common import for views
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
# from .customPage import CustomPagination
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime, date,time, timedelta
from django.db import transaction
from django.conf import settings
from django.http import QueryDict
import json
import pandas as pd
from django.utils.dateparse import parse_date
import redis
from django.core.cache import cache
from util.redis_publisher import RedisPublisher
from config.models import WS_URLS_DB
from util.trigger_ws_redis_pub import trigger_ws_redis_pub
from util.base_model_viewset import BaseModelViewSet

import util.utils_func as Util
import util.cache_manager as CacheManager
from util.trigger_ws_redis_pub import trigger_ws_redis_pub
from util.base_model_viewset import BaseModelViewSet
import util.cache_manager as CacheManager

import os