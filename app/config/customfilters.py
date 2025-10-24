# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from . import models as Config_Models

# class ElevatorFilter(filters.FilterSet):
#     from_최초설치년 = filters.NumberFilter(field_name='최초설치일자', lookup_expr='year__gte')
#     to_최초설치년 = filters.NumberFilter(field_name='최초설치일자', lookup_expr='year__lte')
#     from_최초설치일자 = filters.DateTimeFilter(field_name='최초설치일자', lookup_expr='gte')
#     to_최초설치일자 = filters.DateTimeFilter(field_name='최초설치일자', lookup_expr='lte')
#     시도 = filters.CharFilter(field_name='시도', lookup_expr='icontains'),
#     시군구 = filters.CharFilter(field_name='시군구', lookup_expr='icontains'),
#     from수량 = filters.NumberFilter(field_name='수량', lookup_expr='gte')
#     # 건물명 = filters.CharFilter(field_name='건물명', lookup_expr='in')
#     # min_price = NumberFilter(field_name='price', lookup_expr='gte')
#     # max_price = NumberFilter(field_name='price', lookup_expr='lte')
#     # robotcategory_name = AllValuesFilter(field_name='robot_category__name')
#     # manufacturer_name = AllValuesFilter(field_name='manufacturer__name')
 
#     class Meta:
#         model = Elevator_Summary
#         fields = ['최초설치일자','시도','시군구','수량']



class Table_Config_Filter(filters.FilterSet):
    table_name = filters.CharFilter(field_name='table__table_name', lookup_expr='exact')
    class Meta:
        model = Config_Models.Table_Config
        fields = ['table__table_name']