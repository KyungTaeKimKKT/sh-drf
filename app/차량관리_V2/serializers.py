"""
Serializers for csv file upload APIs
"""
from django.db.models import Sum
from rest_framework import serializers

from . import models

import pandas as pd


class 차량관리_기준정보_Serializer(serializers.ModelSerializer):
    관리자수 = serializers.SerializerMethodField()
    관리자_ids = serializers.SerializerMethodField()
    사용자_datas = serializers.SerializerMethodField()

    class Meta:
        model = models.차량관리_기준정보
        fields = [ f.name for f in model._meta.fields] + ['관리자수','관리자_ids','사용자_datas']
        read_only_fields = ['id']
        
    def get_관리자수(self, obj):
        return models.차량관리_사용자.objects.filter(차량관리_기준정보_fk=obj).count()        
    
    def get_관리자_ids(self, obj):
        return [ user_fk for user_fk in models.차량관리_사용자.objects.filter(차량관리_기준정보_fk=obj).values_list('user_fk', flat=True) ]

    def get_사용자_datas(self, obj):
        qs = models.차량관리_사용자.objects.filter(차량관리_기준정보_fk=obj)
        serializer = 차량관리_사용자_Serializer(qs, many=True)
        return serializer.data



class 차량관리_운행DB_Serializer(serializers.ModelSerializer):
    차량번호 = serializers.SerializerMethodField()
    차량번호_data = serializers.SerializerMethodField()

    class Meta:
        model = models.차량관리_운행DB
        fields = [ f.name for f in model._meta.fields] + ['차량번호','차량번호_data']
        read_only_fields = ['id'] 

    def get_차량번호(self, obj):
        return obj.차량번호_fk.차량번호
    
    def get_차량번호_data(self, obj):
        return 차량관리_기준정보_Serializer(obj.차량번호_fk).data
    

class 차량관리_사용자_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.차량관리_사용자
        fields = '__all__'
        read_only_fields = ['id']

class 차량관리_selector_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.차량관리_selector_DB
        fields = '__all__'
        read_only_fields = ['id']

