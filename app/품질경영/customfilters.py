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


class CS_Claim_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # el_info_fk = filters.NumberFilter(field_name='el_info_fk', method = 'filter_by_el_info_fk')
    진행현황 = filters.CharFilter(field_name='진행현황', lookup_expr='contains')
    부적합유형 = filters.CharFilter(field_name='부적합유형', lookup_expr='contains')
    등록일_From = filters.DateFilter(field_name='등록일', lookup_expr='gte')
    등록일_To = filters.DateFilter(field_name='등록일', lookup_expr='lte')
    완료일_From = filters.DateFilter(field_name='완료일', lookup_expr='gte')
    완료일_To = filters.DateFilter(field_name='완료일', lookup_expr='lte')
    등록자 = filters.CharFilter(field_name='등록자_fk__user_성명', lookup_expr='contains')
    완료자 = filters.CharFilter(field_name='완료자_fk__user_성명', lookup_expr='contains')

    el수량_From = filters.NumberFilter(field_name='el수량', lookup_expr='gte')
    el수량_To = filters.NumberFilter(field_name='el수량', lookup_expr='lte')

    차수_From = filters.NumberFilter(field_name='차수', lookup_expr='gte')
    차수_To = filters.NumberFilter(field_name='차수', lookup_expr='lte')

    품질비용_From = filters.NumberFilter(field_name='품질비용', lookup_expr='gte')
    품질비용_To = filters.NumberFilter(field_name='품질비용', lookup_expr='lte')

    활동현황 = filters.CharFilter(field_name='cs_activity_set__활동현황', method='filter_by_Activity_활동현황')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Received parameters:", self.data)

    class Meta:
        model = models.CS_Claim
        fields = [ 'ids',  '진행현황','부적합유형','el수량_From', 'el수량_To', 
                  '품질비용_From', '품질비용_To', '등록일_From', '등록일_To', '완료일_From', '완료일_To',
                  '등록자', '완료자', '차수_From', '차수_To', '활동현황']  

    def filter_by_Activity_활동현황(self, queryset, name, value):
        print ( self, queryset, name, value)
        if value is not None:
            return queryset.filter(cs_activity_set__활동현황__contains=value)

class CS_Claim_Activity_FilterSet(CS_Claim_FilterSet):
    pass

    # class Meta:
    #     model = models.CS_Activity
    #     fields = [ 'ids',  'claim_fk']  



class CS_Activity_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    claim_fk = filters.NumberFilter(method = 'filter_by_claim_fk')

    class Meta:
        model = models.CS_Activity
        fields = [ 'ids', 'claim_fk']  

    def filter_by_claim_fk(self, queryset, name, value):
        if value is not None:
            return queryset.filter(claim_fk=value)

class CS_Activity_File_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    activity_fk = filters.NumberFilter(method = 'filter_by_activity_fk')

    class Meta:
        model = models.CS_Activity_File
        fields = [ 'ids', 'activity_fk']  

# class 작업지침_DB_FilterSet(filters.FilterSet):
#     수량_From = filters.NumberFilter(field_name='수량', lookup_expr='gte')
#     수량_To = filters.NumberFilter(field_name='수량', lookup_expr='lte')
#     납기일_From = filters.DateFilter(field_name='납기일', lookup_expr='gte')
#     납기일_To = filters.DateFilter(field_name='납기일', lookup_expr='lte')
#     작성일_From = filters.DateFilter(field_name='작성일', lookup_expr='gte')
#     작성일_To = filters.DateFilter(field_name='작성일', lookup_expr='lte')
#     담당 = filters.CharFilter(field_name='담당', lookup_expr='contains')
#     진행현황 = filters.CharFilter(field_name='진행현황', lookup_expr='contains')
#     고객요청사항 = filters.CharFilter(field_name='고객요청사항', lookup_expr='contains')
#     고객성향 = filters.CharFilter(field_name='고객성향', lookup_expr='contains')
#     특이사항 = filters.CharFilter(field_name='특이사항', lookup_expr='contains')
#     집중점검항목 = filters.CharFilter(field_name='집중점검항목', lookup_expr='contains')
#     검사요청사항 = filters.CharFilter(field_name='검사요청사항', lookup_expr='contains')
#     Rev = filters.NumberFilter(field_name='Rev', lookup_expr='exact')
#     is_배포 = filters.BooleanFilter(field_name='is_배포', lookup_expr='exact')
#     is_valid = filters.BooleanFilter(field_name='is_valid', lookup_expr='exact')

#     영업담당자 = filters.CharFilter(field_name='영업담당자_fk__user_성명', lookup_expr='contains')
#     작성자 = filters.CharFilter(field_name='작성자_fk__user_성명', lookup_expr='contains')

#     고객사 = filters.CharFilter( method='filter_by_고객사')
#     구분 = filters.CharFilter ( method='filter_by_구분' )
 
#     class Meta:
#         model = models.작업지침
#         fields = ['수량','납기일', '고객사', '구분', '작성일', '영업담당자_fk', '작성자_fk', '담당', '진행현황', 
#                   '고객요청사항', '고객성향', '특이사항', '집중점검항목', '검사요청사항', 'Rev', 'is_배포', 'is_valid']     

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         print("Received parameters:", self.data)

#     def filter_by_고객사(self, queryset, name, value):
#         if value is not None:
#             고객사list = ['현대','OTIS', 'TKE', '기타']
#             if value == '기타':
#                 return queryset.exclude( 고객사__in = ['현대','OTIS', 'TKE'])
#             return queryset.filter(고객사=value)
        
#     def filter_by_구분(self, queryset, name, value):
#         if value is not None:
#             구분list = ['NE','MOD', '기타']
#             if value == '기타':
#                 return queryset.exclude( 구분__in = ['NE','MOD'])
#             return queryset.filter(구분=value)


class CS_Claim_File_FilterSet(filters.FilterSet, FilterSet_Utils):
    ids = filters.CharFilter(method = 'filter_by_ids')
    # 구분 = filters.CharFilter ( field_name='구분', lookup_expr='contains')

    class Meta:
        model = models.CS_Claim_File
        fields = [ 'ids']  

