from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date
from elevator_info.models import Elevator_Summary_WO설치일

import uuid
from websocket import create_connection
import json
# from 기준정보.models import 고객사_DB

# class 고객사_DB(models.Model):
#     고객사_id = models.CharField(max_length=20, default='')    
#     고객사_표시명 = models.CharField(max_length=20, default='') 
#     is_영업디자인 =  models.BooleanField(blank=True, null=True, default=False)
#     is_MBO =  models.BooleanField(blank=True, null=True, default=False)
    
#     def publish(self):
#         self.published_date = timezone.now()
#         self.save()

#     def __str__(self):
#         return self.고객사_id, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
# # 순서가 중요, 뒤에 고객사_DB Class를 사용하기 위해 앞에 class 선언 필
# # db model을 수정하면 admin.py , 실제 db도 확인     
# 고객사_choice = [(choice.고객사_id, choice.고객사_표시명) for choice in 고객사_DB.objects.filter(is_영업디자인=True) ]
#접수디자이너_choice = [(choice.user_성명, choice.user_성명) for choice in User.objects.filter(is_디자인의뢰_완료자=True).filter(is_디자인의뢰_관리자=False) ]

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    now = datetime.now()
    return ( '영업-디자인관리/영업image/' + instance.현장명 +f'/{now.year}-{now.month}-{now.day}/'+ filename) 

def 의뢰_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    now = datetime.now()
    return ( '영업-디자인관리/영업image/' + f'/의뢰파일/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

def 완료_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    now = datetime.now()
    return ( '영업-디자인관리/디자인image/'+ f'/완료파일/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/' + filename) 

    


class 의뢰file(models.Model):
    file = models.FileField(upload_to=의뢰_directory_path, max_length=254, null=True, blank=True)

@receiver(models.signals.post_save, sender=의뢰file)
def 의뢰file_post_save_receiver(sender, instance, **kwargs):
    print ( 'signal dispatcher : post_save', sender, instance )
    ws = create_connection("ws://mes.swgroup.co.kr:9998/broadcast/db_monitor/")
    ws.send (  json.dumps(  
                {
                    "type":"broadcast",
                    "sender":"system",
                    "message": f"{str(instance.id)} saving message",
                    "send_time" :  datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }, ensure_ascii=False
                ) 
            ) 


    ws.close()

    



class 완료file(models.Model):
    file = models.FileField(upload_to=완료_directory_path, max_length=254, null=True, blank=True)

class 디자인의뢰(models.Model):
    # group_fks = models.ForeignKey ( Group의뢰, blank=True, null=True, on_delete=models.CASCADE )
    현장명_fk = models.ManyToManyField( Elevator_Summary_WO설치일 ,blank=True , related_name='el현장명+')    
    구분 = models.CharField(max_length=20,  null=True)
    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    고객사 = models.CharField(max_length=20,  default='')
    #고객사 = models.CharField(max_length=20, choices=고객사_choice, default='')    #현장명
    현장명 = models.TextField(blank=True, null=True)       # 의뢰내용
    el수량 = models.IntegerField (blank=True, null=True)
    운행층수 = models.IntegerField (blank=True, null=True)
    비고 = models.TextField(blank=True, null=True)       #비고
    상세내용 = models.TextField(blank=True, null=True)   # 특이사항 : db에 manual로 column 생성
    영업담당자 = models.CharField(max_length=20,blank=True, null=True)
    샘플의뢰여부 = models.BooleanField(blank=True, null=True)
    의뢰여부=models.BooleanField(blank=True, null=True)
    의뢰일 = models.DateTimeField(  blank=True, null=True)
       
    완료요청일 = models.DateTimeField( blank=True, null=True)
    등록일 = models.DateTimeField( default=timezone.now)
    접수일 = models.DateTimeField( blank=True, null=True)

    sales_user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='sales_user_fk' )
    designer_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING ,blank=True, null=True ,related_name='designer_user_fk' )

    접수디자이너=models.CharField(max_length=20, blank=True, null=True)  #default='')
    접수여부=models.BooleanField(blank=True, null=True)
    완료디자이너=models.CharField(max_length=20,blank=True, null=True)
    완료여부=models.BooleanField(blank=True, null=True)
    완료일 = models.DateTimeField( blank=True, null=True)
 
    upload_path_1 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    upload_path_2 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    upload_path_3 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    upload_path_4 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    upload_path_5 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    upload_path_6 = models.FileField(upload_to=user_directory_path, max_length=254, null=True, blank=True)
    
    의뢰차수 = models.IntegerField (blank=True, null=True)
    재의뢰사유 = models.CharField(max_length=254, blank=True, null=True)
    첨부파일수 = models.IntegerField (blank=True, null=True)
    완료파일수 = models.IntegerField (blank=True, null=True)

    등록_weekno = models.IntegerField( blank=True, null=True, default=0)
    접수_weekno = models.IntegerField( blank=True, null=True, default=0)
    완료_weekno = models.IntegerField( blank=True, null=True, default=0)

    temp_group_id = models.IntegerField( blank=True, null=True)

    의뢰file_fks = models.ManyToManyField(의뢰file ,blank=True , related_name='의뢰file+' )
    완료file_fks = models.ManyToManyField(완료file ,blank=True , related_name='완료file+' )

    # 완료file_fks = models.ManyToManyField(완료file, blank=True , related_name='완료file_fks+')
 
    def __str__(self):
        return self.현장명
    
    def save(self, *args, **kwargs):
        if self.등록일 : self.등록_weekno = self.등록일.isocalendar()[1]
        if self.접수일 : self.접수_weekno = self.접수일.isocalendar()[1]
        if self.완료일 : self.완료_weekno = self.완료일.isocalendar()[1]
        # if self.접수여부 == None : self.접수여부 = False
        # if self.완료여부 == None : self.완료여부 = False
        uploadPaths = ['upload_path_1', 'upload_path_2','upload_path_3','upload_path_4','upload_path_5','upload_path_6']
        count = 0
        for f in self._meta.get_fields():
            if f.name in uploadPaths : 
                if getattr(self, f.name): count +=1
        # print ( type(self.의뢰file_fks), self.의뢰file_fks)
        # self.첨부파일수 = len(self.의뢰file_fks)
        # self.완료파일수 = len(self.완료file_fks)

        super().save(*args, **kwargs)

 

class Group의뢰 ( models.Model):
    현장명 = models.CharField(max_length=250, blank=True, null=True)
    group = models.ManyToManyField( 디자인의뢰, blank=True , related_name='group+')   