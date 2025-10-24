from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Sum , functions, Q, QuerySet

from datetime import date, datetime, timedelta

from users.models import User, Api_App권한


# ic.disable()
#     
class 차량관리_권한INFO(models.Model):
    user_fk   = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_fk', help_text="차량 관리 담당자입니다.")
    
    is_차량관리_조회자= models.BooleanField(default=True, help_text = "법인 차량 전체를 조회합니다.")
    is_차량관리_사용자= models.BooleanField(default=True, help_text = "차량관리_기준정보에 등록된 차량에 대해서만 조회 및 사용 등록합니다.")
    is_차량관리_관리자= models.BooleanField(default=True, help_text = "차량관리 전체를 관리합니다..")
    
    
class 차량관리_기준정보(models.Model):
    ### 삭제 대상
    user_fk   = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_fk', help_text="차량 관리 담당자입니다.", null=True, blank=True)
    
    법인명 = models.CharField(max_length=15, blank=True, null=True, default='')
    차종 = models.CharField(max_length=20, blank=True, null=True, default='')
    차량번호 = models.CharField(max_length=15, blank=True, null=True, default='')
    타이어규격 = models.CharField(max_length=15, blank=True, null=True, default='')
    공급업체 = models.CharField(max_length=15, blank=True, null=True, default='')
    차량가격 = models.IntegerField( blank=True, null=True, default=0 )
    보증금   = models.IntegerField( blank=True, null=True, default=0 )
    대여료_VAT포함  = models.IntegerField( blank=True, null=True, default=0 )
    약정운행거리  = models.IntegerField( blank=True, null=True, default=0 , help_text="단위 km입니다.")
    초과거리부담금  = models.FloatField( blank=True, null=True, default=0 , help_text="단위 원/km입니다.")
    시작일 = models.DateField( default=timezone.now().date() )
    종료일 = models.DateField( default=timezone.now().date() )
    
    is_exist= models.BooleanField(default=True)

    view_users_m2m = models.ManyToManyField( User , related_name='_view_users', null=True, blank=True)
    write_users_m2m = models.ManyToManyField( User , related_name='_write_users', null=True, blank=True)
    admin_users_m2m = models.ManyToManyField( User , related_name='_admin_users', null=True, blank=True)

@receiver( models.signals.m2m_changed, sender=차량관리_기준정보.admin_users_m2m.through )
@receiver( models.signals.m2m_changed, sender=차량관리_기준정보.write_users_m2m.through )
def 차량관리_기준정보_m2m_changed(sender, instance:차량관리_기준정보, action, **kwargs):   
    ic ( 'signal dispatcher : m2m_changed', sender, instance , action)
    if 'post_add' in action : 
        _inst = Api_App권한.objects.get (id=175 )
        사용자list = _inst.user_pks.all()
        ic ( 사용자list )
        for user in instance.write_users_m2m.all():
            if user not in 사용자list : 
                _inst.user_pks.add ( user )
        for user in instance.admin_users_m2m.all():
            if user not in 사용자list : 
                _inst.user_pks.add ( user )
    elif 'post_remove' in action:
        all_users = []
        for obj in 차량관리_기준정보.objects.filter( is_exist=True ):
            all_users += [user for user in obj.write_users_m2m.all() ]
            all_users += [user for user in obj.admin_users_m2m.all() ]
        all_users = list ( set(all_users) )
        _inst = Api_App권한.objects.get (id=175 )
        사용자list = _inst.user_pks.all()
        ic ( all_users, 사용자list )
        _inst.user_pks.set( all_users )



@receiver( models.signals.m2m_changed, sender=차량관리_기준정보.admin_users_m2m.through )
def 차량관리_기준정보_m2m_changed(sender, instance:차량관리_기준정보, action, **kwargs):
    if 'post' in action:
        ic ( 'signal dispatcher : m2m_changed', sender, instance , action )
    
class 차량관리_운행DB(models.Model):
    차량번호_fk = models.ForeignKey(차량관리_기준정보, on_delete=models.DO_NOTHING, db_column='차량번호_fk' , help_text='차량번호 foreign-key입니다')
    일자 = models.DateTimeField( default=datetime.now() )
    주행거리 = models.IntegerField( default=0 , help_text= "정비일 기준 주행거리(km)입니다" )
    정비금액 = models.IntegerField(  default=0 , help_text= "정비금액입니다." )
    정비사항 = models.TextField ( default='')
    비고 = models.TextField ( blank=True, null=True, default='')
    관련근거 = models.CharField(max_length=30, default='' )
    담당자  = models.CharField (max_length=15, blank=True, null=True, default='' , help_text='이력을 위해 정적 필드 영역입니다.')
    수정자_fk = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, default='', on_delete=models.CASCADE, db_column='수정자_fk' )

    
class 차량관리_selector_DB(models.Model):
    구분 = models.CharField(max_length=15, blank=True, null=True, default='', help_text='selector DB에 구분요소로, 예로 법인, 공급업체 입니다.')
    DB_저장_id =  models.CharField(max_length=15, blank=True, null=True, default='', help_text='DB에 저장될 id로, 예로 상기 법인이 법인이면, (주)신우하이테크, (주)신우폴리텍스 입니다.')
    selector_표시명=  models.CharField(max_length=15, blank=True, null=True, default='', help_text='상기 id에 맞는 사용자에게 보여주는 이름입니다.')


    