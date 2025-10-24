# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from .models import (
    ISSUE_리스트_DB,
    개인_리스트_DB, 
    전기사용량_DB,
)

class 개인_리스트_DB_Filter(filters.FilterSet):
    시작일 = filters.DateFilter(field_name='일자', lookup_expr='gte')
    종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
 
    class Meta:
        model = 개인_리스트_DB
        fields = ['일자']

class 조직_리스트_DB_Filter(filters.FilterSet):
    시작일 = filters.DateFilter(field_name='일자', lookup_expr='gte')
    종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
 
    class Meta:
        model = ISSUE_리스트_DB
        fields = ['일자']

class 전기사용량_DB_Filter(filters.FilterSet):
    시작일 = filters.DateFilter(field_name='일자', lookup_expr='gte')
    종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
    year = filters.NumberFilter (field_name='일자', lookup_expr='year')
    month = filters.NumberFilter(field_name='일자', lookup_expr='month')

    class Meta:
        model = 전기사용량_DB
        fields = ['일자']

from .models  import 휴일_DB
class 휴일_DB_Filter(filters.FilterSet):
    year = filters.NumberFilter (field_name='휴일', lookup_expr='year')
    month = filters.NumberFilter(field_name='휴일', lookup_expr='month')
    시작일 = filters.DateFilter ( field_name='휴일', lookup_expr='gte')
    종료일 = filters.DateFilter ( field_name='휴일', lookup_expr='lte')

    def filter_queryset(self, queryset):
        # print("필터 적용 전 쿼리셋:", queryset.values_list('휴일', flat=True))
        filtered_queryset = super().filter_queryset(queryset)
        # print("필터 적용 후 쿼리셋:", filtered_queryset.values_list('휴일', flat=True))
        return filtered_queryset

    class Meta:
        model = 휴일_DB
        fields = ['휴일']