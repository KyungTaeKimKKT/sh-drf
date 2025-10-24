"""
Serializers for scraping
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from .models import (
    Hour_Schedule,
    App,
)

from util.serializer_for_m2m import Serializer_m2m

class App_Serializer(serializers.ModelSerializer):
    MODEL = App

    class Meta:
        model = App
        # extra_fields =  ['고객사','job_name','생산형태','제품분류','공정','작업명','소재','치수','계획수량']
        # fields =[f.name for f in model._meta.fields] +extra_fields
        fields = '__all__'
        read_only_fields = ['id'] 

class Hour_Schedule_Serializer(serializers.ModelSerializer):
    MODEL = Hour_Schedule
    class Meta:
        model =  Hour_Schedule
        # extra_fields =  ['고객사','job_name','생산형태','제품분류','공정','작업명','소재','치수','계획수량']
        # fields =[f.name for f in model._meta.fields] +extra_fields
        fields = '__all__'
        read_only_fields = ['id'] 


# class NEWS_DB_Serializer(serializers.ModelSerializer):
#     MODEL = NEWS_DB

#     class Meta:
#         model = NEWS_DB
#         fields = '__all__'
#         read_only_fields = ['id'] 


# class NEWS_Table_Head_DB_Serializer(serializers.ModelSerializer):

#     class Meta:
#         model = NEWS_Table_Head_DB
#         fields = '__all__'
#         read_only_fields = ['id'] 


# class NEWS_LOG_DB_Serializer(serializers.ModelSerializer):

#     class Meta:
#         model = NEWS_LOG_DB
#         fields = '__all__'
#         read_only_fields = ['id'] 