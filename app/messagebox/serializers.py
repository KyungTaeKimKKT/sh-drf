"""
Serializers for 작업지침
"""
from django.conf import settings
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone

from users.models import Api_App권한, User
from .models import (
    Chat_Room,
    Chat_내용,
    Chat_file,
)

from users.serializers import UserSerializer
# from elevator_info.models import Elevator_Summary,Elevator_Summary_WO설치일
# from elevator_info.serializers import Summary_WO설치일_Serializer


class Chat_Room_Serializer(serializers.ModelSerializer):
    참가자 = UserSerializer(many=True)

    class Meta:
        model = Chat_Room
        fields =[f.name for f in Chat_Room._meta.fields] +['참가자']
        read_only_fields = ['id'] 
    
    def __init__(self, instance=None, data=..., **kwargs):
        self.참가자 = kwargs.pop('참가자', None)
        super().__init__(instance, data, **kwargs)

    def create(self, validated_data):
        __instance = Chat_Room.objects.create (**validated_data)
        if ( self.참가자 ) : 
            __instance.참가자.clear()
            for id in self.참가자 :
                __instance.참가자.add(id)

        return __instance
 
    # https://stackoverflow.com/questions/50654337/django-writable-nested-serializers-update
    def update(self, instance, validated_data):
        user_pks = validated_data.pop('user_pks',[])
        if (user_pks):  instance.user_pks.set(user_pks)
        # if user_pks is not None:
        #     instance.user_pks.set(user_pks )
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class Chat_내용_Serializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField(method_name='_get_sender_name')
    발송시간 = serializers.SerializerMethodField(method_name='_get_발송시간')
    message_type = serializers.SerializerMethodField(method_name='_get_message_type')

    class Meta:
        model = Chat_내용
        fields =[f.name for f in Chat_내용._meta.fields] + ['sender_name', '발송시간', 'message_type']
        read_only_fields = ['id'] 

    def _get_sender_name(self, instance):
        return instance.user_fk.user_성명
    
    def _get_발송시간(self, instance):
        return instance.기록시간
    
    def _get_message_type(self, instance):
        return instance.type
    

class Chat_file_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Chat_file
        fields =[f.name for f in Chat_file._meta.fields] 
        read_only_fields = ['id'] 