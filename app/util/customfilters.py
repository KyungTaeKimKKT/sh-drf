# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters
from 작업지침.models import (    
    작업지침, 
)
from 생산지시.models import (
    생산지시,
)
# from serial.models import (
#     SerialDB,
# )

from 망관리.models import (
    망관리_DB,
)

class 작업지침_DB_FilterSet(filters.FilterSet):
    납기일_From일자 = filters.DateFilter(field_name='납기일', lookup_expr='gte')
    납기일_To일자 = filters.DateFilter(field_name='납기일', lookup_expr='lte')
    작성일_From일자 = filters.DateFilter(field_name='작성일', lookup_expr='gte')
    작성일_To일자 = filters.DateFilter(field_name='작성일', lookup_expr='lte')
    고객사 = filters.CharFilter(field_name='고객사', lookup_expr='icontains')
    구분 = filters.CharFilter (field_name='구분', lookup_expr='icontains')
 
    class Meta:
        model = 작업지침
        fields = ['납기일', '고객사', '구분', '작성일']

class 생산지시_DB_FilterSet(작업지침_DB_FilterSet):
    # https://www.reddit.com/r/django/comments/k29fik/djangofilters_manytomany_field_returning/
    납기일_From일자 = filters.DateFilter(field_name='도면정보_fks__납기일_Door', method='filter_gte')
    납기일_To일자 = filters.DateFilter(field_name='도면정보_fks__납기일_Door', method='filter_lte')
    작성일_From일자 = filters.DateFilter(field_name='생산지시일', lookup_expr='gte')
    작성일_To일자 = filters.DateFilter(field_name='생산지시일', lookup_expr='lte')
    고객사 = filters.CharFilter(field_name='고객사', lookup_expr='icontains')
    구분 = filters.CharFilter (field_name='구분', lookup_expr='icontains')
    생산형태 = filters.CharFilter(field_name='생산형태', lookup_expr='icontains' )

    class Meta:
        model = 생산지시
        fields = ['도면정보_fks',  
                  '생산지시일', '고객사','구분',]
        
    def filter_gte(self, queryset, name, value):
        return queryset.filter(도면정보_fks__납기일_Door__gte = value).distinct()

    def filter_lte(self, queryset, name, value):
        return queryset.filter(도면정보_fks__납기일_Door__lte = value).distinct()

# class Serial_DB_FilterSet(filters.FilterSet):
#     serial = filters.CharFilter(field_name='serial', method='filter_exact')

#     class Meta:
#         model = SerialDB
#         fields = ['serial']
    
#     def filter_exact(self, queryset, name, value):
#         # print ( name, value )
#         return queryset.filter(serial = value)

class 망관리_FilterSet(filters.FilterSet):
    망번호 = filters.CharFilter(field_name='망번호', lookup_expr='exact')
    고객사 = filters.CharFilter ( field_name='고객사', lookup_expr='contains')
    From일자 = filters.DateFilter(field_name='등록일', lookup_expr='gte')
    To일자 = filters.DateFilter(field_name='등록일', lookup_expr='lte')
    의장종류 = filters.CharFilter(field_name='의장종류', lookup_expr='contains')
    # 망번호 = filters.CharFilter(field_name='망번호', method='filter_exact')
    # 고객사 = filters.CharFilter ( field_name='고객사', method='filter_contains')

    class Meta:
        model = 망관리_DB
        fields = ['망번호','고객사', '등록일','의장종류']
    
    def filter_exact(self, queryset, name, value):
        # print ( name, value )
        return queryset.filter(망번호 = value)

    def filter_contains(self, queryset, name, value):
        print ( name, value )
        return queryset.filter(고객사__contains = value)
    
from elevator_info.models import Elevator_Summary_WO설치일
class Elevator_Info_FilterSet(filters.FilterSet):
    시도 = filters.CharFilter(field_name='시도', lookup_expr='contains')
    From수량 = filters.NumberFilter(field_name='수량', lookup_expr='gte')
    To수량 = filters.NumberFilter(field_name='수량', lookup_expr='lte')
    시작일 = filters.DateFilter(field_name='최초설치일자', lookup_expr='gte')
    종료일 = filters.DateFilter(field_name='최초설치일자', lookup_expr='lte')

    class Meta:
        model = Elevator_Summary_WO설치일
        fields = ['수량', '최초설치일자', '시도']

from elevator_info.models import Elevator
class Elevator_승강기협회_FilterSet(filters.FilterSet):
    시도 = filters.CharFilter(field_name='시도', lookup_expr='contains')
    # From수량 = filters.NumberFilter(field_name='수량', lookup_expr='gte')
    # To수량 = filters.NumberFilter(field_name='수량', lookup_expr='lte')
    From일자 = filters.DateFilter(field_name='최초설치일자', lookup_expr='gte')
    To일자 = filters.DateFilter(field_name='최초설치일자', lookup_expr='lte')

    class Meta:
        model = Elevator
        fields = [ '최초설치일자', '시도']



from scraping.models import NEWS_DB
class NEWS_DB_FilterSet(filters.FilterSet):
    정부기관 = filters.CharFilter(field_name='정부기관', lookup_expr='contains')
    구분 = filters.CharFilter(field_name='구분', lookup_expr='contains')

    class Meta:
        model = NEWS_DB
        fields = [ '정부기관', '구분']


from 생산모니터링.models_외부 import 생산계획실적
class 생산계획실적_BG용_FilterSet(filters.FilterSet):
    # start_time = filters.DateTimeFilter(field_name='start_time',lookup_expr='exact')
    start_time = filters.DateTimeFilter(field_name='start_time', method="filter_start_with")

    class Meta:
        model = 생산계획실적
        fields = ['start_time']

    def filter_start_with(self, queryset, name, value):
        print ('name:', name, '    value:',value, value.date() )
        return queryset.filter(start_time__date__startswith = value.date() )


from 영업mbo.models import 년간보고_지사_구분
class 영업mbo_년간보고_지사_구분_FilterSet(filters.FilterSet):
    매출년도 = filters.NumberFilter(field_name='매출년도', lookup_expr='exact')
    부서 = filters.CharFilter (field_name='부서', lookup_expr='exact')
    구분 = filters.CharFilter (field_name='구분', lookup_expr='exact')
    분류 = filters.CharFilter (field_name='분류', lookup_expr='exact') 

    class Meta:
        model = 년간보고_지사_구분
        fields = ['매출년도', '부서','구분','분류']

from 영업mbo.models import 년간보고_개인별
class 영업mbo_년간보고_개인별_FilterSet(filters.FilterSet):
    매출년도 = filters.NumberFilter(field_name='매출년도', lookup_expr='exact')
    부서 = filters.CharFilter (field_name='부서', lookup_expr='exact')
    구분 = filters.CharFilter (field_name='구분', lookup_expr='exact')
    분류 = filters.CharFilter (field_name='분류', lookup_expr='exact') 

    class Meta:
        model = 년간보고_개인별
        fields = ['매출년도', '부서','구분','분류']

from 영업mbo.models import 년간보고_지사_고객사
class 영업mbo_년간보고_지사_고객사_FilterSet(filters.FilterSet):
    매출년도 = filters.NumberFilter(field_name='매출년도', lookup_expr='exact')
    부서 = filters.CharFilter (field_name='부서', lookup_expr='exact')
    고객사 = filters.CharFilter (field_name='고객사', lookup_expr='exact')
    분류 = filters.CharFilter (field_name='분류', lookup_expr='exact') 

    class Meta:
        model = 년간보고_지사_고객사
        fields = ['매출년도', '부서','고객사','분류']


from users.models import Api_App권한
class Api_App권한_FilterSet(filters.FilterSet):
    div = filters.CharFilter(field_name='div', lookup_expr='contains')
    name = filters.CharFilter(field_name='name', lookup_expr='contains')
    is_Actvie = filters.BooleanFilter(field_name='is_Active', lookup_expr='exact')
    is_Run = filters.BooleanFilter(field_name='is_Run', lookup_expr='exact')
    user_pks = filters.CharFilter(field_name='user_pks__user_성명', lookup_expr='contains')

    class Meta:
        model = Api_App권한
        fields = ['div', 'name','is_Active','is_Run', 'user_pks']

from users.models import Api_App권한
class Api_App사용자_FilterSet(filters.FilterSet):
    div = filters.CharFilter(field_name='div', lookup_expr='contains')
    name = filters.CharFilter(field_name='name', lookup_expr='contains')
    is_Actvie = filters.BooleanFilter(field_name='is_Active', lookup_expr='exact')
    is_Run = filters.BooleanFilter(field_name='is_Run', lookup_expr='exact')
    user_pks = filters.CharFilter(field_name='user_pks__user_성명', lookup_expr='contains')
    is_dev = filters.BooleanFilter(field_name='is_dev', lookup_expr='exact')

    class Meta:
        model = Api_App권한
        fields = ['div', 'name','is_Active','is_Run', 'user_pks', 'is_dev']


from 공지요청사항.models import 요청사항_DB
class 요청사항_DB_FilterSet(filters.FilterSet):
    제목 = filters.CharFilter(field_name='제목', lookup_expr='contains')
    내용 = filters.CharFilter(field_name='내용', lookup_expr='contains')
    is_완료 = filters.BooleanFilter(field_name='is_완료', lookup_expr='exact')
    요청등록일 = filters.DateFilter(field_name='요청등록일', lookup_expr='gte')

    class Meta:
        model = 요청사항_DB
        fields = ['제목', '내용','is_완료','요청등록일']

from 공지요청사항.models import 공지사항
class 공지사항_FilterSet(filters.FilterSet):
    제목 = filters.CharFilter(field_name='제목', lookup_expr='contains')
    공지내용 = filters.CharFilter(field_name='내용', lookup_expr='contains')
    is_Popup = filters.BooleanFilter(field_name='is_Popup', lookup_expr='exact')
    시작일 = filters.DateFilter(field_name='popup_시작일', lookup_expr='gte')
    종료일 = filters.DateFilter(field_name='popup_종료일', lookup_expr='lte')

    class Meta:
        model = 공지사항
        fields = ['제목', '공지내용','is_Popup','popup_시작일','popup_종료일']