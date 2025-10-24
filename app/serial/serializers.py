"""
Serializers for Serial
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta

from django.utils import timezone

from . import models

class SerialDB_Serializer(serializers.ModelSerializer):

    class Meta:
        model = models.SerialDB
        fields = '__all__'

class SerialHistory_Serializer(serializers.ModelSerializer):
    스캔유형_display = serializers.CharField(source='get_스캔유형_display', read_only=True)
    
    class Meta:
        model = models.SerialHistory
        fields = '__all__'
