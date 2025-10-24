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
    정부기관_DB,
    NEWS_DB,
    NEWS_Table_Head_DB,
    NEWS_LOG_DB,
)

from util.serializer_for_m2m import Serializer_m2m

class 정부기관_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = 정부기관_DB
        # extra_fields =  ['고객사','job_name','생산형태','제품분류','공정','작업명','소재','치수','계획수량']
        # fields =[f.name for f in model._meta.fields] +extra_fields
        fields = '__all__'
        read_only_fields = ['id'] 


class NEWS_DB_Serializer(serializers.ModelSerializer):
    MODEL = NEWS_DB

    class Meta:
        model = NEWS_DB
        fields = '__all__'
        read_only_fields = ['id'] 


class NEWS_Table_Head_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = NEWS_Table_Head_DB
        fields = '__all__'
        read_only_fields = ['id'] 


class NEWS_LOG_DB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = NEWS_LOG_DB
        fields = '__all__'
        read_only_fields = ['id'] 