from django.db import models
from django.conf import settings
import uuid
import os
import json, requests
from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re



class System_Alarm (models.Model):
    type_choices = [('message', 'message'), ('alarm', 'alarm'), ('notice', 'notice'), ('error', 'error'), ('warning', 'warning'), ('success', 'success'), ('info', 'info')]
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='sender_set')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='receiver_set')
    main_type = models.CharField(max_length=20, null=True, choices=type_choices)
    sub_type = models.CharField(max_length=20, null=True, blank=True)
    subject = models.CharField(max_length=250, null=True, blank=True)
    message = models.JSONField(null=True, blank=True)

    send_time = models.DateTimeField(null=True)
    read_time = models.DateTimeField(null=True)
    
    is_read = models.BooleanField(default=False)
    is_send = models.BooleanField(default=False)
    is_delete = models.BooleanField(default=False)
    is_save = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Chat_Room(models.Model):
    제목 = models.CharField(max_length=100, blank=True, null=True)
    참가자 = models.ManyToManyField( settings.AUTH_USER_MODEL )

class Chat_내용(models.Model):
    chatroom_fk = models.ForeignKey(Chat_Room, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    user_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    기록시간 = models.DateTimeField(null=True)
    type = models.CharField ( max_length=20, null=True)


def Chat_file_directory_path(instance, filename):
    now = datetime.now()
    return ( f'chat/{instance.chatroom_fk.id}/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 


class Chat_file(models.Model):
    chatroom_fk = models.ForeignKey(Chat_Room, on_delete=models.CASCADE)
    file = models.FileField(upload_to=Chat_file_directory_path,null=True)