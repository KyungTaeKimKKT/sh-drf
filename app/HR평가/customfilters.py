# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from . import models, models_old

class FilterSet_Utils:

    def filter_by_ids(self, queryset, name, value):
        if value is not None:
            # values_list = json.loads( value )
            # print ( self, values_list, type(values_list))
            values_list = value.split(',')
            return queryset.filter(id__in=values_list)

class 평가체계_DB_Filter(filters.FilterSet):
    평가설정_fk = filters.NumberFilter(field_name='평가설정_fk__id', lookup_expr='exact')
    is_참여 = filters.BooleanFilter ( field_name='is_참여', lookup_expr='exact')
  
    class Meta:
        model = models.평가체계_DB
        fields = ['평가설정_fk', 'is_참여']

class 역량항목_DB_Filter(filters.FilterSet):
    평가설정_fk = filters.NumberFilter(field_name='평가설정_fk__id', lookup_expr='exact')
    구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.역량항목_DB
        fields = [ '평가설정_fk', '구분']

class 평가결과_DB_Filter(filters.FilterSet, FilterSet_Utils):
    평가설정_fk = filters.NumberFilter(field_name='평가체계_fk__평가설정_fk__id', lookup_expr='exact')
    평가체계_fk = filters.NumberFilter(field_name='평가체계_fk__id', lookup_expr='exact')
    is_submit = filters.BooleanFilter(field_name='is_submit', lookup_expr='exact')

    ids = filters.CharFilter(method = 'filter_by_ids')

    class Meta:
        model = models.평가결과_DB
        fields = [ '평가체계_fk', 'is_submit', 'ids']

class 역량_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    등록자_fk = filters.NumberFilter(field_name='등록자_fk', lookup_expr='exact')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.역량_평가_DB
        fields = [ 'ids', '등록자_fk']


        
class 성과_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.성과_평가_DB
        fields = [ 'ids']

class 특별_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.특별_평가_DB
        fields = [ 'ids']



class 종합평가_결과_Old_Filter(filters.FilterSet, FilterSet_Utils):
    평가제목_fk = filters.NumberFilter(field_name='평가제목_fk__id', lookup_expr='exact')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model =  models_old.종합평가_결과_Old
        fields = [ '평가제목_fk' ]    