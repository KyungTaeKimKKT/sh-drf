"""
Serializers for 공지요청사항
"""
from django.conf import settings
from rest_framework import serializers
from django.core import serializers as core_serializer
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from . import models
from .models import (
    Log_login,  
    Log_사용App, 
    사내IP,
    사내IP_PING결과,
    사내IP_PING결과_Image,
)
# from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
# from elevator_info.serializers import Summary_WO설치일_Serializer
# from 작업지침.serializers import 작업지침_Serializer
import json

def model_to_dict_custom(instance):
    model_dict = {}
    # Iterate through the model instance's fields
    for field in instance._meta.fields:
        field_name = field.name
        if ( 'NCR_fk' in field_name) :   field_value = instance.NCR_fk_id
        else :   field_value = getattr(instance, field_name)
        # Convert special types if needed (e.g., datetime to string)
        if hasattr(field_value, 'strftime'):
            field_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
        model_dict[field_name] = field_value
    return model_dict

def _getClientIP(obj):
    x_forwarded_for = obj.context.get('request').META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = obj.context.get('request').META.get('REMOTE_ADDR')
    return ip    

class Log_login_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Log_login
        fields =[f.name for f in Log_login._meta.fields] 
        read_only_fields = ['id'] 

    def create(self, validated_data):
        validated_data['ip'] = _getClientIP(self)
        return Log_login.objects.create(**validated_data)
    
class Client_App_Access_Log_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Client_App_Access_Log
        fields = '__all__'
        read_only_fields = ['id']


class Log_사용App_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Log_사용App
        fields =[f.name for f in Log_사용App._meta.fields] 
        read_only_fields = ['id'] 

    def create(self, validated_data):
        validated_data['ip'] = _getClientIP(self)
        return Log_사용App.objects.create(**validated_data)
    
class 사내IP_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 사내IP
        fields =[f.name for f in 사내IP._meta.fields] 
        read_only_fields = ['id'] 
        extra_kwargs = {
            'MAC_주소': {'allow_blank': True, 'required': False},
            '비고': {'allow_blank': True, 'required': False},
            'Category': {'allow_blank': True, 'required': False},
            '상위IP': {'allow_blank': True, 'required': False},
            'host_이름': {'allow_blank': True, 'required': False},
            'host_설명': {'allow_blank': True, 'required': False},

        }

class 사내IP_PING결과_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 사내IP_PING결과
        fields =[f.name for f in 사내IP_PING결과._meta.fields] 
        read_only_fields = ['id'] 


    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['사내IP_fk'] = instance.사내IP_fk.IP_주소
        # response['사내IP_fk'] = 사내IP_Serializer(instance.사내IP_fk).data
        return response


class 사내IP_PING결과_Image_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 사내IP_PING결과_Image
        fields = '__all__'
        # fields =[f.name for f in 사내IP_PING결과._meta.fields] 
        read_only_fields = ['id'] 


# class 공지사항_Reading_Serializer(serializers.ModelSerializer):
#     # file_fks = 부적합_file_Serializer(many=True, required=False)
#     # 품질비용 =  serializers.SerializerMethodField(method_name='_get품질비용')

#     class Meta:
#         model = 공지사항_Reading
#         fields =[f.name for f in 공지사항_Reading._meta.fields] #+ ['file_fks','품질비용'] 
#         read_only_fields = ['id'] 
#         validators = []  # Remove a default "unique together" constraint.

#     # def to_representation(self, instance):
#     #     response = super().to_representation(instance)        
#     #     response['작성자_fk'] = instance.작성자_fk.user_성명
#     #     return response
    

#     # def __init__(self, *args, **kwargs):
#     #     file_fks = kwargs.pop('부적합상세', None)
#     #     품질비용 = kwargs.pop('품질비용', None)

#     #     self.file_fks = file_fks
#     #     self.품질비용 = 품질비용
#     #     super().__init__(*args, **kwargs)

#     # def _get품질비용(self, instance):
#     #     try : 
#     #         품질비용instance = 품질비용.objects.get(NCR_fk=instance.id)  
#     #         return model_to_dict_custom( 품질비용instance )                   
#     #         # return model_to_dict_custom( 품질비용instance )
#     #         return 품질비용_Serializer(품질비용instance).data
#     #     except : 
#     #         return ''

#     def create(self, validated_data):
#         validated_data['ip'] = self._getClientIP()
#         return 공지사항_Reading.objects.create(**validated_data)

#     # def update(self, instance, validated_data):
#     #     print ( "update내 validated-data :  최초 - ", validated_data )
#     #     print ( '--------------------------------------\n\n\n')

#     #     super().update(instance=instance, validated_data=validated_data)
        
#     #     if ( self.file_fks):
#     #         instance.file_fks.clear()
#     #         for file in self.file_fks:
#     #             # file.pop('id','')
#     #             instance.file_fks.add( 부적합_file.objects.create(file=file) )  
          
#     #     if ( self.품질비용 ):
#     #         품질비용instance, _created = 품질비용.objects.get_or_create( NCR_fk=instance.id )
#     #         for k, v in self.품질비용.items():
#     #             setattr ( 품질비용instance, k, v)
#     #         품질비용instance.save()

#     #     # if ( self.결재내용_fks ):
#     #         # instance.결재내용_fks.clear()
#     #         # 기안자 = {
#     #         #     '결재자' :  self.context.get('request', None).user,
#     #         #     '결재결과' : True,
#     #         #     '결재의견' : '결재의뢰 합니다.',
#     #         #     '결재일' : timezone.now(),
#     #         #     '의뢰일' : timezone.now(),
#     #         # }
#     #         # instance.결재내용_fks.add (결재내용.objects.create( **기안자 ) )
#     #         # for 결재자 in  self.결재내용_fks:
#     #         #     instance.결재내용_fks.add (결재내용.objects.create(결재자=User.objects.get(id=결재자), 의뢰일= 기안자['의뢰일'] ))

#     #         # instance.진행현황 = self._get_진행현황(instance)
#     #         # instance.save()
        
#     #     return NCR.objects.get(id=instance.id)
#     def _getClientIP(self):
#         x_forwarded_for = self.context.get('request').META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = self.context.get('request').META.get('REMOTE_ADDR')
#         return ip


#     def _get_inputFields(self, instance):
#         print (self.fields)
#         return self.fields
#     # def _get_현장명_fk_full(self, instance):
#     #     return False

#     # def _get_group_의뢰차수(self, instance):
#     #     return Group생산지시.objects.filter(group = instance.id ).count()
    
#     def _get_첨부file수(self, instance):
#         return instance.첨부file_fks.count()
    
#     def _get_진행현황(self, instance):
#         if ( not instance.결재내용_fks.count() ): return '작성중'
        
#         for 결재instance in instance.결재내용_fks.all() :
#             if ( 결재instance.결재결과 is not None ) :
                
#                 if( not 결재instance.결재결과 ): return '반려'

#         for 결재instance in instance.결재내용_fks.all() :
#             if ( 결재instance.결재결과 is None) : return '진행중'

#         return '완료'        


class ApiAccessLog_Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApiAccessLog
        fields = [f.name for f in model._meta.fields]
        read_only_fields = ['id']