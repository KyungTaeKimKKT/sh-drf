"""
Serializers for csv file upload APIs
"""
from django.db.models import Sum
from rest_framework import serializers

from . import models

import pandas as pd


class 차량관리_기준정보_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.차량관리_기준정보
        fields = '__all__'
        read_only_fields = ['id']


class 차량관리_운행DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.차량관리_운행DB
        fields = '__all__'
        read_only_fields = ['id']
   
    def to_representation(self, instance:models.차량관리_운행DB):
        data = super().to_representation(instance)
        for name in ['차량번호', '법인명', '차종','공급업체','시작일','종료일','약정운행거리']:
            data[name] = getattr(instance.차량번호_fk, name)

        return data

class 차량관리_selector_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.차량관리_selector_DB
        fields = '__all__'
        read_only_fields = ['id']

