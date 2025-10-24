# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters



from .models import NEWS_DB
class NEWS_DB_FilterSet(filters.FilterSet):
    시작일 = filters.DateFilter(field_name='등록일', lookup_expr='gte')
    종료일 = filters.CharFilter(field_name='등록일', lookup_expr='lte')
    # is_완료 = filters.BooleanFilter(field_name='is_완료', lookup_expr='exact')
    # 요청등록일 = filters.DateFilter(field_name='요청등록일', lookup_expr='gte')

    class Meta:
        model = NEWS_DB
        fields = ['등록일']