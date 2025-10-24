"""
Serializers for csv file upload APIs
"""
from __future__ import annotations
from typing import List, Dict, Any
from django.db.models import Sum
from rest_framework import serializers

from . import models,  models_old

import pandas as pd
from collections import defaultdict



class 역량평가사전_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.역량평가사전_DB
        fields = '__all__'
        read_only_fields = ['id']



class 역량_평가_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.역량_평가_DB
        fields = '__all__'
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        instance : models.역량_평가_DB
        data = super().to_representation(instance)
        data['구분'] = instance.fk.구분
        data['항목'] = instance.fk.항목
        data['정의'] = instance.fk.정의
        return data

class 역량항목_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.역량항목_DB
        fields = '__all__'
        read_only_fields = ['id']

class 성과_평가_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.성과_평가_DB
        fields = '__all__'
        read_only_fields = ['id']



class 특별_평가_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.특별_평가_DB
        fields = '__all__'
        read_only_fields = ['id']


class 평가설정_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.평가설정_DB 
        fields = '__all__'
        read_only_fields = ['id', '등록일']


class 평가체계_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.평가체계_DB 
        fields = '__all__'
        read_only_fields = ['id']

#### 25-5.27 신규


# class 역량평가_DB_Serializer_V2(serializers.ModelSerializer):
#     # 역량평가_api_datas = serializers.SerializerMethodField()
#     class Meta:
#         model = models.역량평가_DB_V2
#         fields = [ f.name for f in model._meta.fields] #+ ['역량평가_api_datas']
#         read_only_fields = ['id']
    
#     def get_역량평가_api_datas(self, instance):
#         qs = models.세부_역량평가_DB_V2.objects.filter(역량평가_fk=instance)
#         return 세부_역량평가_DB_Serializer_V2(qs, read_only=True, many=True).data

# class 세부_역량평가_DB_Serializer_V2(serializers.ModelSerializer):
#     항목_data = serializers.SerializerMethodField()

#     class Meta:
#         model = models.세부_역량평가_DB_V2
#         fields = [ f.name for f in model._meta.fields] + ['항목_data']
#         read_only_fields = ['id']
    
#     def get_항목_data(self, instance):
#         return 역량평가_항목_DB_Serializer_V2(instance.항목, read_only=True).data

# class 성과평가_DB_Serializer_V2(serializers.ModelSerializer):
#     # 성과평가_api_datas = serializers.SerializerMethodField()    
#     class Meta:
#         model = models.성과평가_DB_V2
#         fields = [ f.name for f in model._meta.fields] #+ ['성과평가_api_datas']
#         read_only_fields = ['id']
    
#     def get_성과평가_api_datas(self, instance):
#         qs = models.세부_성과평가_DB_V2.objects.filter(성과평가_fk=instance)
#         return 세부_성과평가_DB_Serializer_V2(qs, read_only=True, many=True).data

# class 세부_성과평가_DB_Serializer_V2(serializers.ModelSerializer):
#     class Meta:
#         model = models.세부_성과평가_DB_V2
#         fields = '__all__'
#         read_only_fields = ['id']

# class 특별평가_DB_Serializer_V2(serializers.ModelSerializer):
#     # 특별평가_api_datas = serializers.SerializerMethodField()    
#     class Meta:
#         model = models.특별평가_DB_V2
#         fields = [ f.name for f in model._meta.fields] #+ ['특별평가_api_datas']
#         read_only_fields = ['id']
    
#     def get_특별평가_api_datas(self, instance):
#         qs = models.세부_특별평가_DB_V2.objects.filter(특별평가_fk=instance)
#         return 세부_특별평가_DB_Serializer_V2(qs, read_only=True, many=True).data

# class 세부_특별평가_DB_Serializer_V2(serializers.ModelSerializer):
#     class Meta:
#         model = models.세부_특별평가_DB_V2
#         fields = '__all__'
#         read_only_fields = ['id']


# class 역량평가_항목_DB_Serializer_V2(serializers.ModelSerializer):
#     항목_이름 = serializers.SerializerMethodField()
#     구분 = serializers.SerializerMethodField()
#     정의 = serializers.SerializerMethodField()

#     class Meta:
#         model = models.역량평가_항목_DB_V2
#         # fields = '__all__'
#         fields =  [f.name for f in model._meta.fields] + ['항목_이름', '구분', '정의']
#         read_only_fields = ['id']

#     def get_항목_이름(self, instance):
#         return instance.항목.항목
#     def get_구분(self, instance):
#         return instance.항목.구분
#     def get_정의(self, instance):
#         return instance.항목.정의


class 평가결과_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.평가결과_DB 
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        instance : models.평가결과_DB
        본인평가_instance =  models.평가결과_DB.objects.get( 평가체계_fk__평가설정_fk = instance.평가체계_fk.평가설정_fk, 
                        평가체계_fk__피평가자=instance.평가체계_fk.피평가자, \
                        평가체계_fk__평가자 = instance.평가체계_fk.피평가자,  평가체계_fk__차수= 0 )
        data = super().to_representation(instance)
        data['피평가자'] = instance.평가체계_fk.피평가자.id

        data['피평가자_성명'] = instance.평가체계_fk.피평가자.user_성명
        data['피평가자_조직'] = instance.평가체계_fk.피평가자.기본조직1
        data['본인평가_id'] = 본인평가_instance.id
        data['본인평가_완료'] = 본인평가_instance.is_submit 
        data['평가설정_fk'] = instance.평가체계_fk.평가설정_fk.id
        return data


class 평가설정DB_Old_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models_old.평가설정DB_Old
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
    

class 종합평가_결과_Old_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models_old.종합평가_결과_Old
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data