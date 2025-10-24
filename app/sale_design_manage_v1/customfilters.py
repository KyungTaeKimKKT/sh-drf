# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters



from .models import 디자인의뢰
class 디자인의뢰_DB_FilterSet(filters.FilterSet):
    고객사 = filters.CharFilter(field_name='고객사', lookup_expr='contains')
    구분 = filters.CharFilter(field_name='구분', lookup_expr='contains')
    # is_완료 = filters.BooleanFilter(field_name='is_완료', lookup_expr='exact')
    # 요청등록일 = filters.DateFilter(field_name='요청등록일', lookup_expr='gte')

    class Meta:
        model = 디자인의뢰
        fields = ['고객사','구분']