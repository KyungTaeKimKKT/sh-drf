from typing import Iterable
from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

from django.utils import timezone
from users.models import User # custom User model import

from datetime import datetime, date

import uuid
# import 생산지시.models as 생지


# def 부적합_directory_path(instance, filename):
#     now = datetime.now()
#     return ( '품질경영/부적합/첨부파일/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

# class 부적합_file( models.Model):
#     file = models.FileField(upload_to=부적합_directory_path, max_length=254, null=True, blank=True)


class 공지사항(models.Model):
    # file_fks =  models.ManyToManyField( 부적합_file )
    
    제목 = models.CharField(max_length=200,  null=True, blank=True)

    시작일 = models.DateField(  default=timezone.now().date())
    종료일 = models.DateField(  default=timezone.now().date())
    공지내용 = RichTextField(null=True)

    is_Popup = models.BooleanField(default=False)
    popup_시작일 = models.DateField(  blank=True, null=True)
    popup_종료일 = models.DateField(  blank=True, null=True)
    popup_대상 = models.CharField(max_length=200, null=True, blank=True)  # 예: app권한 id 목록
 

class 공지사항_Reading( models.Model) :
    공지사항_fk = models.ForeignKey( 공지사항,  on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey( User,  on_delete=models.CASCADE, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField (null=True)

    def save(self, *args, **kwargs):
        self.timestamp = timezone.now()        
        super().save(*args, **kwargs) 
        return self

def user_directory_path_요청사항(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    return ( '공지요청사항/요청사항/' + str(uuid.uuid4())+'/'+ filename) 

class File_for_Request (models.Model):
    요청사항_fk = models.ForeignKey("요청사항_DB", on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to=user_directory_path_요청사항, max_length=254, null=True, blank=True )

class 요청사항_DB( models.Model ):        
    등록자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,blank=True)
    # 등록자 = models.CharField(max_length=20,blank=True, null=True)
    제목 = models.CharField(max_length=100, default='')    #현장명
    요청구분 = models.CharField(max_length=20, null=True, blank=True)
    내용 = models.TextField(blank=True, null=True, default='')      
    요청등록일 = models.DateField( null=True, blank=True, default=timezone.now().date() )
 
    처리내용 = models.TextField(blank=True, null=True, default='')      
    처리일자 =  models.DateField(blank=True, null=True)
    
    is_완료 =models.BooleanField(blank=True, null=True, default=False)

