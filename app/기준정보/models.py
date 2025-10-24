
from django.conf import settings
from django.db import models
from django.utils import timezone
#from users.models import User,고객사_DB # custom User model import


    
# # 순서가 중요, 뒤에 고객사_DB Class를 사용하기 위해 앞에 class 선언 필
# # db model을 수정하면 admin.py , 실제 db도 확인     
# 고객사_choice = [(choice.고객사_id, choice.고객사_표시명) for choice in 고객사_DB.objects.filter(is_영업디자인=True) ]
# 접수디자이너_choice = [(choice.user_성명, choice.user_성명) for choice in User.objects.filter(is_디자인의뢰_완료자=True).filter(is_디자인의뢰_관리자=False) ]

class 의장종류_DB(models.Model):
    의장종류_id     = models.CharField(max_length=20, default='')    
    의장종류_표시명 =  models.CharField(max_length=20, default='') 
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    #is_MBO =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.의장종류_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 할부치수_DB(models.Model):
    할부치수_id     = models.CharField(max_length=20, default='')    
    할부치수_표시명 =  models.CharField(max_length=20, default='') 
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.할부치수_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 품명_DB(models.Model):
    품명_id     = models.CharField(max_length=20, default='')    
    품명_표시명 =  models.CharField(max_length=20, default='') 
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.품명_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO

class 망사_DB(models.Model):
    망사_id     = models.CharField( max_length=20,blank=True, null=True, default='')
    망사_표시명 = models.CharField( max_length=20, blank=True, null=True, default='')
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.망사_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 사용구분_DB(models.Model):
    사용구분_id     = models.CharField(max_length=20, default='')  
    사용구분_표시명 = models.CharField(max_length=20, default='')  
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.사용구분_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 고객사_DB(models.Model):
    고객사_id = models.CharField(max_length=20, default='')    
    고객사_표시명 = models.CharField(max_length=20, default='') 
    is_영업디자인 =  models.BooleanField(blank=True, null=True, default=False)
    is_MBO =  models.BooleanField(blank=True, null=True, default=False)
    is_망관리 =  models.BooleanField(blank=True, null=True, default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.고객사_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    