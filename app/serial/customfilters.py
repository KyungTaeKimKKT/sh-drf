# https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html
from rest_framework import generics
from django_filters import rest_framework as filters



from . import models as serial_models

class Seiral_History_DB_FilterSet(filters.FilterSet):
    serial = filters.CharFilter(field_name='serial_fk__serial', lookup_expr='exact')
    # 구분 = filters.CharFilter(field_name='구분', lookup_expr='contains')
    # is_완료 = filters.BooleanFilter(field_name='is_완료', lookup_expr='exact')
    # 요청등록일 = filters.DateFilter(field_name='요청등록일', lookup_expr='gte')

    class Meta:
        model = serial_models.SerialHistory
        fields = ['serial_fk',]