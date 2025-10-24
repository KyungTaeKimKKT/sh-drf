from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from django.conf import settings
from django.dispatch import receiver

import datetime
import uuid
import util.utils_func as Utils


# ic.disable()

class TestUserDB(models.Model):
    user_mailid = models.CharField(
        verbose_name='user_mailid',
        max_length=20,
        unique=True,
    )
    user_성명 = models.CharField( max_length=20, blank=True )
    user_직책 = models.CharField( max_length=20, blank=True ) 
    user_직급 = models.CharField( max_length=10, blank=True )

class CompanyDB(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True, null=True)
    협력업종 = models.CharField(max_length=100, blank=True, null=True, help_text='자사, 원자재, 반제품,제품' )
    is_active = models.BooleanField(default=True)
    # 추가적인 필드들을 여기에 정의할 수 있습니다.

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, user_mailid, password=None):
        if not user_mailid:
            raise ValueError('메일id는 필수사항입니다.')

        user = self.model(
            user_mailid = user_mailid
            #user_mailid=self.normalize_user_mailid(user_mailid),

        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_mailid,  password):
        user = self.create_user(
            user_mailid,
            password=password,

        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    user_mailid = models.CharField(
        verbose_name='user_mailid',
        max_length=20,
        unique=True,
    )
    user_성명 = models.CharField( max_length=20, blank=True )
    user_직책 = models.CharField( max_length=20, blank=True ) 
    user_직급 = models.CharField( max_length=10, blank=True )
    
    기본조직1 = models.CharField( max_length=20, blank=True )
    기본조직2 = models.CharField( max_length=20, blank=True )
    기본조직3 = models.CharField( max_length=20, blank=True )
    
    MBO_표시명_부서 = models.CharField( max_length=20, blank=True )

    Company_fk = models.ForeignKey(CompanyDB, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    is_mbo_조회자 = models.BooleanField(default=False)
    is_mbo_사용자 = models.BooleanField(default=False)
    is_mbo_관리자 = models.BooleanField(default=False)
    
    is_일일보고_조회자 = models.BooleanField(default=False)
    is_일일보고_사용자 = models.BooleanField(default=False)
    is_일일보고_관리자 = models.BooleanField(default=False)
    
    is_망관리_조회자 = models.BooleanField(default=False)
    is_망관리_사용자 = models.BooleanField(default=False)
    is_망관리_관리자 = models.BooleanField(default=False)
    
   
    is_디자인의뢰_조회자 = models.BooleanField(default=False)
    is_디자인의뢰_의뢰자 = models.BooleanField(default=False)
    is_디자인의뢰_접수자 = models.BooleanField(default=False)
    is_디자인의뢰_완료자 = models.BooleanField(default=False)
    is_디자인의뢰_관리자 = models.BooleanField(default=False)
    is_디자인의뢰_대시보드_영업 = models.BooleanField(default=False)
    is_디자인의뢰_대시보드_디자인 = models.BooleanField(default=False)
    
    is_차량관리_조회자 = models.BooleanField(default=False)
    is_차량관리_사용자 = models.BooleanField(default=False)
    is_차량관리_관리자 = models.BooleanField(default=False)
    
    #보고순서= models.IntegerField( blank=True, null=True, default=0, unique=True, help_text='unique 정수 5자리 입니다. ')
    
    objects = UserManager()

    USERNAME_FIELD = 'user_mailid'
    #REQUIRED_FIELDS = ['user_성명']

    def __str__(self):
        return f"{self.user_성명} - {self.user_mailid}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
 
def help_page_directory_path(instance, filename):
    now = datetime.datetime.now()
    return ( 'helppage/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

### 실제 사용되는 model임
class Api_App권한(models.Model):
    div = models.CharField(max_length=100,  default='', blank=True, null=True )
    name = models.CharField(max_length=100,  default='', blank=True, null=True )
    url = models.CharField(max_length=250,  default='', blank=True, null=True )
    api_uri = models.CharField(max_length=250,  default='', blank=True, null=True )
    api_url = models.CharField(max_length=250,  default='', blank=True, null=True )

    #### 표시하는 이름
    표시명_구분 = models.CharField(max_length=250,  default='', blank=True, null=True )
    표시명_항목 = models.CharField(max_length=250,  default='', blank=True, null=True )

    비고 = models.CharField(max_length=250,  default='', blank=True, null=True )
    등록일 = models.DateTimeField(auto_now_add=True)
    is_Active = models.BooleanField(default=False)  # 관리자가 배포 유무 판단.
    is_Run = models.BooleanField(default=False)      # 프로그램상 자동으로 배포 유무 판단.
    순서 = models.IntegerField(default = 10000)     # 보여주는 순서

    is_dev = models.BooleanField(default=True)
    help_page = models.FileField(upload_to=help_page_directory_path, max_length=254, null=True, blank=True)
    info_title = models.CharField(max_length=200,  default='', blank=True, null=True )
    
    # 테이블 설정을 위한 추가 필드
    TO_MODEL = models.CharField(max_length=250, default='', blank=True, null=True, help_text='모델 경로 (예: app_name.ModelName)')
    TO_Serializer = models.CharField(max_length=250, default='', blank=True, null=True, help_text='시리얼라이저 경로 (예: app_name.SerializerName)')

    # 7-10 추가
    lazy_attrs = models.JSONField(default=dict)
    App_Menus = models.JSONField(default=dict)
    Table_Menus = models.JSONField(default=dict)

    def save(self, *args, **kwargs):
        # 표시명_구분이 없으면 div 값을 가져옴
        if not self.표시명_구분 and self.div:
            self.표시명_구분 = self.div
            
        # 표시명_항목이 없으면 name 값을 가져옴
        if not self.표시명_항목 and self.name:
            self.표시명_항목 = self.name
            
        super(Api_App권한, self).save(*args, **kwargs)


# 새로운 중간 모델 추가 : m2m 관리자 model임
class Api_App권한_User_M2M(models.Model):
    app_권한 = models.ForeignKey(Api_App권한, on_delete=models.CASCADE, related_name='app_권한_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_pks')
    
    # 추가 필드 (필요에 따라)
    # 부여일시 = models.DateTimeField(auto_now_add=True)
    # 부여자 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_permissions')
    # is_active = models.BooleanField(default=True)
    
    class Meta:
        # 중복 방지를 위한 unique_together
        unique_together = ('app_권한', 'user')
            
    def __str__(self):
        return f"{self.user.user_mailid} - {self.app_권한.name}"   
    
class App권한_User_M2M_Snapshot(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()

# class api_User권한(models.Model):
#     user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     name = models.CharField(max_length=20,  default='', blank=True, null=True )
#     mail = models.CharField(max_length=20,  default='', blank=True, null=True )
#     app_pks = models.TextField(blank=True, null=True) 
#     비고 = models.CharField(max_length=250,  default='', blank=True, null=True )
#     등록일 = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         super(App권한, self).save(*args, **kwargs) 

class App권한(models.Model):
    div = models.CharField(max_length=100,  default='', blank=True, null=True )
    name = models.CharField(max_length=100,  default='', blank=True, null=True )
    url = models.CharField(max_length=250,  default='', blank=True, null=True )
    user_pks = models.TextField(blank=True, null=True) 
    user_names= models.TextField(blank=True, null=True) 
    비고 = models.CharField(max_length=250,  default='', blank=True, null=True )
    등록일 = models.DateTimeField( default=timezone.now)
    is_Active = models.BooleanField(default=False)  # 관리자가 배포 유무 판단.
    is_Run = models.BooleanField(default=True)      # 프로그램상 자동으로 배포 유무 판단.
    순서 = models.IntegerField(default = 10000)     # 보여주는 순서
    
    def save(self, *args, **kwargs):
        self.등록일 = timezone.now()
        super(App권한, self).save(*args, **kwargs)

class User권한(models.Model):
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20,  default='', blank=True, null=True )
    mail = models.CharField(max_length=20,  default='', blank=True, null=True )
    app_pks = models.TextField(blank=True, null=True) 
    비고 = models.CharField(max_length=250,  default='', blank=True, null=True )
    등록일 = models.DateTimeField( default=timezone.now)

    def save(self, *args, **kwargs):
        self.등록일 = timezone.now()
        super(App권한, self).save(*args, **kwargs) 


def error_video_directory_path(instance, filename):
    now = datetime.datetime.now()
    return ( 'error_video/' + f'/{now.year}-{now.month}-{now.day}/'+ str(uuid.uuid4()) +'/'+ filename) 

class ErrorLog(models.Model):

    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    app_fk = models.ForeignKey(Api_App권한, on_delete=models.CASCADE, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    error_time = models.DateTimeField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)

    file = models.FileField(upload_to=error_video_directory_path, max_length=254, null=True, blank=True)

    OS = models.CharField(max_length=100,  default='')
    버젼 = models.DecimalField(max_digits=5, decimal_places=2,  default=0.01)

    def save(self, *args, **kwargs):
        self.error_time = timezone.now()
        super(ErrorLog, self).save(*args, **kwargs)

logo_directory_path = 'portal_logo/'

class Portal_Info(models.Model):
    name = models.CharField(max_length=100,  default='', blank=True, null=True , help_text='portal 이름')
    url = models.CharField(max_length=250,  default='', blank=True, null=True , help_text='portal 접근 url')
    logo = models.ImageField(upload_to=logo_directory_path, max_length=254, null=True, blank=True, help_text='portal 로고')
    is_active = models.BooleanField(default=True)
    description = models.TextField(default='', blank=True, null=True )
    order = models.IntegerField(default=0, help_text='보여주는 순서')

    def __str__(self):
        return self.name


class Portal_Permission(models.Model):
    """ user 별로, 접근 가능한 portal 정보를 저장합니다.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portal_info = models.ForeignKey(Portal_Info, on_delete=models.CASCADE)  
    is_active = models.BooleanField(default=True)
