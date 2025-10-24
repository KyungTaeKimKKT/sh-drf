# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from . import models

import json

# def filter_by_ids( queryset, name, value):
#     print ( value, name )
#     if value is not None:
#         print( type(value), value )
#         # values_list = json.loads( value )
#         # print ( self, values_list, type(values_list))
#         values_list = value.split(',')
#         return queryset.filter(id__in=values_list)

class 사용자등록_DB_Filter(filters.FilterSet):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
 
    class Meta:
        model = models.사용자등록_DB
        fields = ['ids']

    def filter_by_ids(self, queryset, name, value):
        if value is not None:
            # values_list = json.loads( value )
            # print ( self, values_list, type(values_list))
            values_list = value.split(',')
            return queryset.filter(id__in=values_list)


class 출하현장_master_DB_Filter(filters.FilterSet):
    고객사 = filters.CharFilter(field_name='고객사', lookup_expr= 'contains')
    구분 = filters.CharFilter(field_name='구분', lookup_expr= 'contains')
    부서 = filters.CharFilter(field_name='부서', lookup_expr= 'contains')
    담당자 = filters.CharFilter(field_name='담당자', lookup_expr= 'contains')
    # 종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
 
    class Meta:
        model = models.출하현장_master_DB
        fields = ['고객사','구분','부서','담당자']

    def filter_by_ids(self, queryset, name, value):
        if value is not None:
            # values_list = json.loads( value )
            # print ( self, values_list, type(values_list))
            values_list = value.split(',')
            return queryset.filter(id__in=values_list)

# class 조직_리스트_DB_Filter(filters.FilterSet):
#     시작일 = filters.DateFilter(field_name='일자', lookup_expr='gte')
#     종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
 
#     class Meta:
#         model = ISSUE_리스트_DB
#         fields = ['일자']

# class 전기사용량_DB_Filter(filters.FilterSet):
#     시작일 = filters.DateFilter(field_name='일자', lookup_expr='gte')
#     종료일 = filters.DateFilter(field_name='일자', lookup_expr='lte')
#     year = filters.NumberFilter (field_name='일자', lookup_expr='year')
#     month = filters.NumberFilter(field_name='일자', lookup_expr='month')

#     class Meta:
#         model = 전기사용량_DB
#         fields = ['일자']

# from .models  import 휴일_DB
# class 휴일_DB_Filter(filters.FilterSet):
#     year = filters.NumberFilter (field_name='휴일', lookup_expr='year')
#     month = filters.NumberFilter(field_name='휴일', lookup_expr='month')

#     class Meta:
#         model = 휴일_DB
#         fields = ['휴일']