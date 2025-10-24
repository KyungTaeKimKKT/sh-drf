"""
Serializers for 생산관리
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from . import models

from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
from elevator_info.serializers import Elevator_Summary_WO설치일_Serializer
from 작업지침.serializers import 작업지침_Serializer
import json
from util.serializer_for_m2m import Serializer_m2m

from 생산지시.models import 생산지시

class 판금처_DB_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.판금처_DB
        fields = '__all__'

class 생산계획_DDay_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.생산계획_DDay
        fields ='__all__'
        read_only_fields = ['id']


class ProductionLine_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductionLine
        fields ='__all__'
        read_only_fields = ['id']

class 생산계획_Schedule_By_Types_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Schedule_By_Types
        fields ='__all__'
        read_only_fields = ['id']


class 생산계획_일정관리_Serializer(serializers.ModelSerializer, Serializer_m2m):

    class Meta:
        model = models.생산계획_일정관리
        fields ='__all__'
        # extra_fields =  ['생산지시_fk_contents', ] #'file1_fk_contents' ,'file2_fk_contents'] 
        # fields =[f.name for f in model._meta.fields] +extra_fields
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance:models.생산계획_일정관리):
        data = super().to_representation(instance)

        ### 생산지시_fk에 대한
        for key in ['고객사','구분','Job_Name','Proj_No'] :
            data[key] = getattr( instance.생산지시_fk, key )
        
        ### schedule_... _fk에 대한
        for  attrName in  ['Door','Cage','JAMB']:
            sch_obj = getattr( instance, f"schedule_{attrName.lower()}_fk")
            data[f"납기일_{attrName}"] = getattr( sch_obj, '출하일' )
    
        # response['생산지시_fk'] = 생산지시_Serializer(instance.생산지시_fk).data
        # response['생산지시_process_fk'] = Process_Serializer(instance.생산지시_process_fk).data
        return data
  
class 생산계획_공정상세_Serializer( serializers.ModelSerializer):

    class Meta:
        model = models.생산계획_공정상세
        fields ='__all__'
        read_only_fields = ['id'] 

    def to_representation(self, instance: models.생산계획_공정상세 ):
        data = super().to_representation(instance)

        ###😀 1. 생산지시_obj
        생산지시_obj = 생산지시.objects.get( process_fks = instance.확정Branch_fk.생산지시_process_fk )
        data['생산지시_fk'] =  생산지시_obj.id
        for key in ['Proj_No', '고객사','구분','Job_Name','지시수량']:
            data[key]  = getattr( 생산지시_obj, key )
        
        ####2. schedule obj
        for key in ['출하_type', '출하일', 'HI일정'] :
            data[key] = getattr ( instance.확정Branch_fk.schedule_fk, key )

        ####3. process obj
        data['계획수량'] =  instance.확정Branch_fk.계획수량 if instance.확정Branch_fk.계획수량 else instance.확정Branch_fk.생산지시_process_fk.수량
        for key in ['치수', '소재', '대표Process', '상세Process','비고']:
            data[key] = getattr( instance.확정Branch_fk.생산지시_process_fk, key )

        ####4, ProductionLine_fk
        for key in ['구분','설비','name']:
            if instance.ProductionLine_fk and hasattr( instance.ProductionLine_fk, key):
                data[key] = getattr ( instance.ProductionLine_fk, key)

        return data


class 생산계획_확정Branch_Serializer( serializers.ModelSerializer):
    공정상세_set = 생산계획_공정상세_Serializer(many=True, read_only=True)

    class Meta:
        model = models.생산계획_확정Branch
        fields ='__all__'
        # extra_fields =  ['생산지시_fk_contents', ] #'file1_fk_contents' ,'file2_fk_contents'] 
        # fields =[f.name for f in model._meta.fields] +extra_fields
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.

    def to_representation(self, instance:models.생산계획_확정Branch):
        data = super().to_representation(instance)

        ###😀 1. 생산지시_obj
        생산지시_obj = 생산지시.objects.get( process_fks = instance.생산지시_process_fk )
        data['생산지시_fk'] =  생산지시_obj.id
        for key in ['Proj_No', '고객사','구분','Job_Name','지시수량']:
            data[key]  = getattr( 생산지시_obj, key )
        
        ####2. schedule obj
        for key in ['출하_type', '출하일', 'HI일정'] :
            data[key] = getattr ( instance.schedule_fk, key )

        ####3. process obj
        data['계획수량'] =  instance.계획수량 if instance.계획수량 else instance.생산지시_process_fk.수량
        for key in ['치수', '소재', '대표Process', '상세Process','비고']:
            data[key] = getattr( instance.생산지시_process_fk, key )
        
        # response['생산지시_fk'] = 생산지시_Serializer(instance.생산지시_fk).data
        # response['생산지시_process_fk'] = Process_Serializer(instance.생산지시_process_fk).data
        return data  

class 생산실적_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.생산실적
        fields ='__all__'
        read_only_fields = ['id']   


class 생산관리_제품완료_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.생산관리_제품완료
        fields ='__all__'
        read_only_fields = ['id']   