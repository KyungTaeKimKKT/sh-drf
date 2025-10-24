# Create your models here.

from django.conf import settings
from django.db import models
from django.utils import timezone
from users.models import User # custom User model import
from 기준정보.models import 의장종류_DB, 할부치수_DB, 품명_DB, 망사_DB, 사용구분_DB, 고객사_DB


def user_directory_path(instance, filename):
    return ( '망관리/패턴파일/' + instance.망번호 +'/'+ filename) 

class 망관리_DB(models.Model):    
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    등록자 = models.CharField(max_length=20,blank=True, null=True)
    망번호 = models.CharField(max_length=20, default='',unique=True) 
    고객사 = models.CharField(max_length=20, default='')    #현장명
    현장명 = models.CharField(max_length=50,blank=True, null=True, default='')       # 의뢰내용
    문양   = models.CharField(max_length=30,blank=True, null=True, default='') 
    의장종류 = models.CharField(max_length=20, default='') 
    할부치수 = models.CharField(max_length=20, default='') 
    품명    = models.CharField(max_length=20, default='') 
    file1 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True, default='')
    file2 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True, default='')
    
    등록일 = models.DateTimeField( default=timezone.now)
    
    망사 = models.IntegerField(blank=True, null=True,  default=0)
    사용구분 = models.CharField(max_length=20, default='') 
    세부내용 = models.TextField(blank=True, null=True)
    
    비고 = models.TextField(blank=True, null=True)       #비고
    검색key = models.CharField(max_length=20, default='')       
    
    is_active =models.BooleanField(blank=True, null=True, default=True)
    폐기사유   =models.CharField(max_length=20, blank=True, null=True, default='') 
    폐기일 = models.DateTimeField( blank=True, null=True, default=timezone.now)
    
    serial = models.IntegerField( blank=True, null=True, default=0)
    is_등록 = models.BooleanField(default=False)
 
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return (self.망번호)
    

class 망관리_DB_폐기사유(models.Model): 
    폐기사유_id     = models.CharField(max_length=20, default='')    
    폐기사유_표시명 =  models.CharField(max_length=20, default='') 
    is_망관리 =  models.BooleanField(blank=True, null=True, default=True)
    #is_MBO =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.폐기사유_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
