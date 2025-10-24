from typing import Iterable
from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User, Api_App권한 # custom User model import

from datetime import datetime, date

import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

#### 25-7-7
class ApiAccessLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    method = models.CharField(max_length=20)
    path = models.TextField()
    query_params = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

#### 25-8-7
class Client_App_Access_Log(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    app_fk = models.ForeignKey(Api_App권한, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, default='running')  # login, logout, running 등

class Log_login(models.Model):
    user_fk = models.ForeignKey( User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField (null=True)
    ip = models.GenericIPAddressField(null=True)
    
    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()        
        super().save(*args, **kwargs) 
        return self


class Log_사용App(models.Model):
    구분 = models.CharField(max_length=20, null=True)
    app = models.CharField(max_length=30, null=True)
    user_fk = models.ForeignKey( User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField (null=True)
    ip = models.GenericIPAddressField(null=True)

    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()        
        super().save(*args, **kwargs) 
        return self

class 사내IP(models.Model):
    Category = models.CharField(max_length=30, null=True)
    # Category_순서 = models.IntegerField()
    IP_주소 = models.GenericIPAddressField(unique=True, null=True)
    host_이름 = models.CharField(max_length=30, null=True)
    host_설명 = models.CharField(max_length=30, null=True)
    MAC_주소 = models.CharField(max_length=30, null=True)
    비고 =  models.CharField(max_length=100, null=True)
    # Group = models.CharField(max_length=30, null=True)
    상위IP = models.GenericIPAddressField(null=True)

    rel_x = models.FloatField(null=True)
    rel_y = models.FloatField(null=True)


class 사내IP_PING결과(models.Model):
    사내IP_fk = models.ForeignKey( 사내IP, on_delete=models.CASCADE, null=True, blank=True)
    결과 = models.BooleanField(default=False)
    timestamp = models.DateTimeField (null=True)
    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()        
        super().save(*args, **kwargs) 
        return self

def ping_img_directory_path(instance, filename):
    now = datetime.now()
    return ( '모니터링/ping_image/' +  str(uuid.uuid4()) +'/'+ filename) 


class 사내IP_PING결과_Image(models.Model):
    file = models.FileField(upload_to=ping_img_directory_path, max_length=254, null=True, blank=True)
    timestamp = models.DateTimeField (null=True)
    
    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()        
        super().save(*args, **kwargs) 


# class 공지사항_Reading( models.Model) :
#     공지사항_fk = models.ForeignKey( 공지사항,  on_delete=models.CASCADE, null=True, blank=True)
#     user = models.ForeignKey( User,  on_delete=models.CASCADE, null=True, blank=True)
#     ip = models.GenericIPAddressField(null=True)
#     timestamp = models.DateTimeField (null=True)

#     def save(self, *args, **kwargs):
#         self.timestamp = timezone.now()        
#         super().save(*args, **kwargs) 
#         return self