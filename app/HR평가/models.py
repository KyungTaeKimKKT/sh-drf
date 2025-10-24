from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date
from elevator_info.models import Elevator_Summary_WO설치일


# ic.disable()

import uuid
from websocket import create_connection
import json

class 역량평가사전_DB(models.Model):
    구분 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="공통역량, 직무역량(공통), 리더십역량 등: 추가 가능") 
    항목 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="열정, 원칙준수 , .....") 
    정의 = models.CharField(max_length=255, blank=True, null=True,default='', help_text="......")
         
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_역량평가사전_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

class 평가설정_DB ( models.Model) :
    제목 = models.CharField(max_length=30, blank=True, null=True)
    시작 = models.DateField ( default=date.today)
    종료 = models.DateField ( default=date.today)
    
    총평가차수 = models.IntegerField( default=2)
    # 평가체계_fk = models.ForeignKey ( 평가체계_DB, on_delete=models.DO_NOTHING , related_name='_평가체계')

    점유_역량 = models.IntegerField ( default = 30)
    점유_성과 = models.IntegerField ( default = 50)
    점유_특별 = models.IntegerField ( default = 20)    

    차수별_점유 = models.JSONField(default={0: 0, 1:50, 2:50})
    차수별_유형 = models.JSONField(default={0:'개별',1:'개별',2:'종합'})
    
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_평가설정_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    is_시작 = models.BooleanField(default=False)
    is_종료 = models.BooleanField(default=False) 

def get_active_평가설정():
    return 평가설정_DB.objects.filter( is_시작=True, is_종료=False ).latest('id')

class 역량_평가_DB(models.Model):
    fk = models.ForeignKey( 역량평가사전_DB, on_delete=models.DO_NOTHING, related_name='역량평가_역량평가사전')
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, related_name='_역량평가_평가설정',null=True, blank=True)
    평가점수 = models.FloatField( null=True, blank=True , default=0.0)

    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_역량_평가_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    def save(self, *args, **kwargs):
        if self.평가설정_fk is None or not isinstance(self.평가설정_fk, 평가설정_DB ):
            self.평가설정_fk = get_active_평가설정()
        super().save(*args, **kwargs)


class 역량평가_DB(models.Model):
    평가체계_fk = models.ForeignKey( "평가체계_DB", on_delete=models.CASCADE, related_name='_역량평가_평가체계', null=True, blank=True, )
    역량평가사전_fk = models.ForeignKey( "역량평가사전_DB", on_delete=models.CASCADE, related_name='_역량평가_역량평가사전', null=True, blank=True, )
    평가점수 = models.FloatField( null=True, blank=True , default=0.0)
    is_submit = models.BooleanField(default=False)

    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

@receiver(models.signals.post_save, sender=역량_평가_DB)
def 역량_평가_DB_changed(sender, instance:역량_평가_DB, **kwargs):
    ic ( 'signal dispatcher : post_save', sender, instance )
    if instance.평가설정_fk.is_시작 and not instance.평가설정_fk.is_종료:
        for _inst in 평가결과_DB.objects.filter( ability_m2m = instance ):
            _inst.save()


class 성과_평가_DB(models.Model):
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, related_name='_성과평가_평가설정',null=True, blank=True)
    과제명 = models.CharField ( max_length=250, blank=True, null=True )
    과제목표 = models.TextField( blank=True, null=True,default='', help_text=".....") 
    성과  = models.TextField( blank=True, null=True,default='', help_text=".....") 
    목표달성률 = models.CharField(max_length=250, blank=True, null=True,default='', help_text=".....")
    실행기간   = models.CharField(max_length=50, blank=True, null=True,default='', help_text=".....")
    가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
    평가점수 = models.FloatField ( default = 0.0)
         
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_성과_평가_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    def save(self, *args, **kwargs):
        if self.평가설정_fk is None or not isinstance(self.평가설정_fk, 평가설정_DB ):
            self.평가설정_fk = get_active_평가설정()
        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = "HR평가_성과_평가_db"  # 기존 테이블과 맞춤

@receiver(models.signals.post_save, sender=성과_평가_DB)
def 성과_평가_DB_changed(sender, instance:성과_평가_DB, **kwargs):
    ic ( 'signal dispatcher : post_save', sender, instance )
    if instance.평가설정_fk.is_시작 and not instance.평가설정_fk.is_종료:
        for _inst in 평가결과_DB.objects.filter( perform_m2m = instance ):
            _inst.save()

class 특별_평가_DB(models.Model):
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, related_name='_특별평가_평가설정',null=True, blank=True)
    구분 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="품질, 혁신 등") 
    성과 = models.TextField(blank=True, null=True, default='', help_text="항목 예시 ") 
    가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
    평가점수 = models.FloatField ( default = 0.0)
         
    등록자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_특별_평가_등록자')
    등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )

    def save(self, *args, **kwargs):
        if self.평가설정_fk is None or not isinstance(self.평가설정_fk, 평가설정_DB ):
            self.평가설정_fk = get_active_평가설정()
        super().save(*args, **kwargs)

@receiver(models.signals.post_save, sender=특별_평가_DB)
def 특별_평가_DB_changed(sender, instance:특별_평가_DB, **kwargs):
    ic ( 'signal dispatcher : post_save', sender, instance )
    if instance.평가설정_fk.is_시작 and not instance.평가설정_fk.is_종료:
        for _inst in 평가결과_DB.objects.filter( special_m2m = instance ):
            _inst.save()


class 역량항목_DB ( models.Model):
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, null=True, blank=True, related_name='_역량평가항목_DB_평가설정')    
    구분 = models.CharField( max_length= 20, null=True, blank=True )
    # 등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now() )
    item_fks = models.ManyToManyField( 역량평가사전_DB, related_name='__item_m2m+')


class 평가체계_DB ( models.Model ):
    평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.CASCADE, related_name='_평가체계_평가설정')
    평가자 =   models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='_평가체계_평가자')
    피평가자 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='_평가체계_피평가자')
    차수 =  models.IntegerField( default=0)
    is_참여 = models.BooleanField( default=True )
    # is_submit = models.BooleanField( default=False )
    
class 평가결과_DB ( models.Model ):
    # 평가설정_fk  =  models.ForeignKey ( 평가설정_DB, on_delete=models.DO_NOTHING , related_name='_평가결과_평가설정')
    평가체계_fk = models.ForeignKey ( 평가체계_DB, on_delete=models.CASCADE, null=True, blank=True , related_name='평가자_평가체계_fk')
    ability_m2m = models.ManyToManyField( 역량_평가_DB , related_name="abilty_m2m" )    
    perform_m2m = models.ManyToManyField( 성과_평가_DB , related_name="perform_m2m" )
    special_m2m = models.ManyToManyField( 특별_평가_DB , related_name="special_m2m" )

    피평가자_평가체계_fk = models.ForeignKey( 평가체계_DB, on_delete=models.CASCADE, null=True, blank=True , related_name='피평가자_평가체계_fk')
    is_submit = models.BooleanField(default=False )

    역량점수 = models.FloatField(default=0)
    성과점수 = models.FloatField(default=0)
    특별점수 = models.FloatField(default=0)
    종합점수 = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        _instance평가설정 = self.평가체계_fk.평가설정_fk
        # ic ( _instance평가설정 , _instance평가설정.차수별_유형, self.평가체계_fk.차수)
        # ic (  _instance평가설정.차수별_유형.get( self.평가체계_fk.차수), _instance평가설정.차수별_유형.get( self.평가체계_fk.차수) == '개별')
        if _instance평가설정.차수별_유형.get( self.평가체계_fk.차수) == '개별' or _instance평가설정.차수별_유형.get( str(self.평가체계_fk.차수) ) == '개별':
            # ic ( '개별')
            try:
                if hasattr(self, 'ability_m2m') and self.ability_m2m.count() > 0:
                    평가점수s = [ _inst.평가점수 for _inst in self.ability_m2m.all() ]
                    self.역량점수 =  round( sum(평가점수s)/len(평가점수s), 2)
                if  hasattr(self, 'perform_m2m') and self.perform_m2m.count() > 0:
                    self.성과점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in self.perform_m2m.all() ] )
                if  hasattr(self, 'special_m2m') and self.special_m2m.count() > 0:
                    self.특별점수 = sum ([ _inst.평가점수*_inst.가중치 / 100 for _inst in self.special_m2m.all() ] )
            except Exception as e:
                ic ( '평가결과-db-save error:', e)

        self.역량점수 = round( self.역량점수, 2)
        self.성과점수 = round( self.성과점수, 2)
        self.특별점수 = round( self.특별점수, 2)
        self.종합점수 = round ( ( self.역량점수*_instance평가설정.점유_역량  + self.성과점수*_instance평가설정.점유_성과 + self.특별점수*_instance평가설정.점유_특별 ) / 100, 2)
        super().save(*args, **kwargs)


#### 5/27 신규
# class 인사평가_결괴_DB(models.Model):
#     평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='_평가체계_fk')
#     역량평가_fk = models.ForeignKey('역량평가_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='_역량평가_fk')
#     성과평가_fk = models.ForeignKey('성과평가_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='_성과평가_fk')
#     특별평가_fk = models.ForeignKey('특별평가_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='_특별평가_fk')
#     is_submit = models.BooleanField(default=False )

# class 역량평가_항목_DB_V2(models.Model):
#     평가설정_fk = models.ForeignKey('평가설정_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_항목_평가설정_fk')
#     항목 = models.ForeignKey('역량평가사전_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_항목_항목')
#     차수 = models.IntegerField(default=0)
    

# class 역량평가_DB_V2(models.Model):
#     평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='역량평가_평가체계_fk')
#     is_submit = models.BooleanField(default=False )
#     평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
#     평가점수 = models.FloatField(default=0)
    
    

# class 세부_역량평가_DB_V2(models.Model):
#     역량평가_fk = models.ForeignKey('역량평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_역량평가_fk')
#     항목 = models.ForeignKey('역량평가_항목_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_역량평가_항목')
#     평가점수 = models.FloatField(default=0)    
    
    
# class 성과평가_DB_V2(models.Model):
#     평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='성과평가_평가체계_fk')
#     is_submit = models.BooleanField(default=False )
#     평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
#     평가점수 = models.FloatField(default=0)
    

# class 세부_성과평가_DB_V2(models.Model):
#     성과평가_fk = models.ForeignKey('성과평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_성과평가_fk')
    
#     과제명 = models.CharField ( max_length=250, blank=True, null=True )
#     과제목표 = models.TextField( blank=True, null=True,default='', help_text=".....") 
#     성과  = models.TextField( blank=True, null=True,default='', help_text=".....") 
#     목표달성률 = models.CharField(max_length=250, blank=True, null=True,default='', help_text=".....")
#     실행기간   = models.CharField(max_length=50, blank=True, null=True,default='', help_text=".....")
#     가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
#     평가점수 = models.FloatField ( default = 0.0)
         
 
#     등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )
    
# class 특별평가_DB_V2(models.Model):
#     평가체계_fk = models.ForeignKey('평가체계_DB', on_delete=models.CASCADE, null=True, blank=True , related_name='특별평가_평가체계_fk')
#     is_submit = models.BooleanField(default=False )
#     평가종류 = models.CharField(max_length=20, blank=True, null=True, default='개별')
#     평가점수 = models.FloatField(default=0)
    
# class 세부_특별평가_DB_V2(models.Model):
#     특별평가_fk = models.ForeignKey('특별평가_DB_V2', on_delete=models.CASCADE, null=True, blank=True , related_name='세부_특별평가_fk')

#     구분 = models.CharField(max_length=15, blank=True, null=True,default='', help_text="품질, 혁신 등") 
#     성과 = models.TextField(blank=True, null=True, default='', help_text="항목 예시 ") 
#     가중치   = models.IntegerField(blank=True, null=True,default=0, help_text=".....")
#     평가점수 = models.FloatField ( default = 0.0)
         
#     등록일 = models.DateTimeField( blank=True, null=True, default=datetime.now )


