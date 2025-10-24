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

class User관리_Filter(filters.FilterSet):
    is_active = filters.BooleanFilter ( field_name='is_active', lookup_expr='exact')
  
    class Meta:
        model = models.User
        fields = ['is_active']

class CompanyDBFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = models.CompanyDB
        fields = ['name']