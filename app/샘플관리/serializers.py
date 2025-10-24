"""
Serializers for 샘플관리
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



class 첨부file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.첨부file
        fields = '__all__' #[f.name for f in 첨부file._meta.fields] 
        read_only_fields = ['id'] 

class 완료file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.완료file
        fields = '__all__' #[f.name for f in 완료file._meta.fields] 
        read_only_fields = ['id'] 

class Process_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.Process
        fields = '__all__' #[f.name for f in Process._meta.fields]
        read_only_fields = ['id'] 

class 샘플관리_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.샘플관리
        fields = '__all__' #[f.name for f in 샘플의뢰._meta.fields] + ['process_fks' , '첨부file_fks', '완료file_fks'] 
        read_only_fields = ['id'] 

    def to_representation(self, instance: models.샘플관리 ):
        data = super().to_representation(instance)      

        data['요청자'] = instance.요청자_fk.user_성명 if instance.요청자_fk else ''
        data['첨부파일'] = instance.첨부file_fks.count()
        data['완료자'] = instance.완료자_fk.user_성명 if instance.완료자_fk else ''
        data['완료파일'] = instance.완료file_fks.count()
        data['첨부파일_URL'] = [ _inst.file.url for _inst in instance.첨부file_fks.all() ]
        data['완료파일_URL'] = [ _inst.file.url for _inst in instance.완료file_fks.all() ]
        data['요청수량'] = sum( [ process.수량  for process in instance.process_fks.all()])

        # data['요청자'] = 샘플의뢰_Serializer(instance.샘플의뢰_fk).data
        return data

# class 샘플의뢰_Serializer(serializers.ModelSerializer):

#     class Meta:
#         model = models.샘플의뢰
#         fields = '__all__' #[f.name for f in 샘플의뢰._meta.fields] + ['process_fks' , '첨부file_fks', '완료file_fks'] 
#         read_only_fields = ['id'] 

#     def __init__(self, *args, **kwargs):
#         if ( fks:= kwargs.pop('fks', None) ):
#             for key, value in fks.items():
#                 self.__setattr__(key, value)

#         super().__init__(*args, **kwargs)

#     def to_representation(self, instance: models.샘플의뢰 ):
#         data = super().to_representation(instance)        
#         data['요청자'] = instance.요청자_fk.user_성명
#         data['첨부파일'] = instance.첨부file_fks.count()

#         # data['요청자'] = 샘플의뢰_Serializer(instance.샘플의뢰_fk).data
#         return data