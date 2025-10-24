# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from . import models

class FilterSet_Utils:

    def filter_by_ids(self, queryset, name, value):
        if value is not None:
            # values_list = json.loads( value )
            # print ( self, values_list, type(values_list))
            values_list = value.split(',')
            return queryset.filter(id__in=values_list)

class 작업지침_DB_FilterSet(filters.FilterSet):
    수량_From = filters.NumberFilter(field_name='수량', lookup_expr='gte')
    수량_To = filters.NumberFilter(field_name='수량', lookup_expr='lte')
    납기일_From = filters.DateFilter(field_name='납기일', lookup_expr='gte')
    납기일_To = filters.DateFilter(field_name='납기일', lookup_expr='lte')
    작성일_From = filters.DateFilter(field_name='작성일', lookup_expr='gte')
    작성일_To = filters.DateFilter(field_name='작성일', lookup_expr='lte')
    담당 = filters.CharFilter(field_name='담당', lookup_expr='contains')
    진행현황 = filters.CharFilter(field_name='진행현황', lookup_expr='contains')
    고객요청사항 = filters.CharFilter(field_name='고객요청사항', lookup_expr='contains')
    고객성향 = filters.CharFilter(field_name='고객성향', lookup_expr='contains')
    특이사항 = filters.CharFilter(field_name='특이사항', lookup_expr='contains')
    집중점검항목 = filters.CharFilter(field_name='집중점검항목', lookup_expr='contains')
    검사요청사항 = filters.CharFilter(field_name='검사요청사항', lookup_expr='contains')
    Rev = filters.NumberFilter(field_name='Rev', lookup_expr='exact')
    is_배포 = filters.BooleanFilter(field_name='is_배포', lookup_expr='exact')
    is_valid = filters.BooleanFilter(field_name='is_valid', lookup_expr='exact')

    영업담당자 = filters.CharFilter(field_name='영업담당자_fk__user_성명', lookup_expr='contains')
    작성자 = filters.CharFilter(field_name='작성자_fk__user_성명', lookup_expr='contains')

    고객사 = filters.CharFilter( method='filter_by_고객사')
    구분 = filters.CharFilter ( method='filter_by_구분' )
 
    class Meta:
        model = models.작업지침
        fields = ['수량','납기일', '고객사', '구분', '작성일', '영업담당자_fk', '작성자_fk', '담당', '진행현황', 
                  '고객요청사항', '고객성향', '특이사항', '집중점검항목', '검사요청사항', 'Rev', 'is_배포', 'is_valid']     

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Received parameters:", self.data)

    def filter_by_고객사(self, queryset, name, value):
        if value is not None:
            고객사list = ['현대','OTIS', 'TKE', '기타']
            if value == '기타':
                return queryset.exclude( 고객사__in = ['현대','OTIS', 'TKE'])
            return queryset.filter(고객사=value)
        
    def filter_by_구분(self, queryset, name, value):
        if value is not None:
            구분list = ['NE','MOD', '기타']
            if value == '기타':
                return queryset.exclude( 구분__in = ['NE','MOD'])
            return queryset.filter(구분=value)


class 작업지침_Process_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.Process
        fields = [ 'ids']  

class 작업지침_의장도_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.의장도
        fields = [ 'ids'] 


        
# class 샘플관리_Process_Filter(filters.FilterSet):
#     평가설정_fk = filters.NumberFilter(field_name='평가설정_fk__id', lookup_expr='exact')
#     is_참여 = filters.BooleanFilter ( field_name='is_참여', lookup_expr='exact')
  
#     class Meta:
#         model = models.평가체계_DB
#         fields = ['평가설정_fk', 'is_참여']

# class 역량항목_DB_Filter(filters.FilterSet):
#     평가설정_fk = filters.NumberFilter(field_name='평가설정_fk__id', lookup_expr='exact')
#     구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

#     class Meta:
#         model = models.역량항목_DB
#         fields = [ '평가설정_fk', '구분']

# class 평가결과_DB_Filter(filters.FilterSet, FilterSet_Utils):
#     평가설정_fk = filters.NumberFilter(field_name='평가체계_fk__평가설정_fk__id', lookup_expr='exact')
#     평가체계_fk = filters.NumberFilter(field_name='평가체계_fk__id', lookup_expr='exact')
#     is_submit = filters.BooleanFilter(field_name='is_submit', lookup_expr='exact')

#     ids = filters.CharFilter(method = 'filter_by_ids')

#     class Meta:
#         model = models.평가결과_DB
#         fields = [ '평가체계_fk', 'is_submit', 'ids']

# class 역량_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
#     ids = filters.CharFilter(method = 'filter_by_ids')
#     등록자_fk = filters.NumberFilter(field_name='등록자_fk', lookup_expr='exact')
#     # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

#     class Meta:
#         model = models.역량_평가_DB
#         fields = [ 'ids', '등록자_fk']


        
# class 성과_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
#     ids = filters.CharFilter(method = 'filter_by_ids')
#     # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

#     class Meta:
#         model = models.성과_평가_DB
#         fields = [ 'ids']

# class 특별_평가_DB_Filter(filters.FilterSet, FilterSet_Utils):
#     ids = filters.CharFilter(method = 'filter_by_ids')
#     # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

#     class Meta:
#         model = models.특별_평가_DB
#         fields = [ 'ids']



# class 종합평가_결과_Old_Filter(filters.FilterSet, FilterSet_Utils):
#     평가제목_fk = filters.NumberFilter(field_name='평가제목_fk__id', lookup_expr='exact')
#     # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

#     class Meta:
#         model =  models_old.종합평가_결과_Old
#         fields = [ '평가제목_fk' ]    