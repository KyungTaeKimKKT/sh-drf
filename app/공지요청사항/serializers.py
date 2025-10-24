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
from .models import (
    공지사항, 
    공지사항_Reading, 
    File_for_Request,
    요청사항_DB,
)
# from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
# from elevator_info.serializers import Summary_WO설치일_Serializer
# from 작업지침.serializers import 작업지침_Serializer
import json


class 공지사항_Serializer(serializers.ModelSerializer):
    reading_count = serializers.SerializerMethodField(method_name='_get_reading_count')
    reading_users = serializers.SerializerMethodField(method_name='_get_reading_users')

    class Meta:
        model = 공지사항
        fields = '__all__'
        read_only_fields = ['id'] 

    def _get_reading_count(self, instance):
        return self._get_qs_reading_users(instance).count()
        
    def _get_reading_users(self, instance) -> list[str]:
        qs = self._get_qs_reading_users(instance)
        return list(set(qs))

    def _get_qs_reading_users(self, instance):
        qs = 공지사항_Reading.objects.filter(
            공지사항_fk=instance,
            user__is_active=True
        ).exclude(user__is_admin=True).values_list('user', flat=True).distinct()
        return qs

class 공지사항_Reading_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 공지사항_Reading
        fields =[f.name for f in 공지사항_Reading._meta.fields] #+ ['file_fks','품질비용'] 
        read_only_fields = ['id'] 
        validators = []  # Remove a default "unique together" constraint.



class 요청사항_DB_Serializer(serializers.ModelSerializer):
    file수 = serializers.SerializerMethodField(method_name='_get_file수', read_only=True)
    files = serializers.SerializerMethodField(method_name='_get_files', read_only=True)
    class Meta:
        model = 요청사항_DB
        fields =[f.name for f in model._meta.fields] + ['file수', 'files']
        read_only_fields = ['id'] 

    def _get_file수(self, instance):
        return File_for_Request.objects.filter(요청사항_fk=instance).count()

    def _get_files(self, instance):
        qs = File_for_Request.objects.filter(요청사항_fk=instance)
        return File_for_Request_Serializer(qs, many=True).data

class File_for_Request_Serializer(serializers.ModelSerializer):

    class Meta:
        model = File_for_Request
        fields = '__all__'
        # fields =[f.name for f in 공지사항._meta.fields] 
        read_only_fields = ['id'] 

