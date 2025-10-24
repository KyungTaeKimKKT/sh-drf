
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta
#   https://stackoverflow.com/questions/12188142/set-minimum-value-for-a-datetimefield
from django.core.exceptions import ValidationError
#from 전사일일업무.utils import 일일업무_util
from users.models import User # custom User model import
# from 기준정보.models import 의장종류_DB, 할부치수_DB, 품명_DB, 망사_DB, 사용구분_DB, 고객사_DB
import uuid
from django.db.models import Q

# from colorfield.fields import ColorField

unique_id = uuid.uuid4().hex

class 대표_보고명_DB(models.Model):
    대표_보고명 = models.CharField(max_length=15,blank=True, null=True)
    대표_보고순서   = models.IntegerField( blank=True, null=True, default=0, unique=True, help_text='unique 정수 5자리 입니다. ')
    user = models.CharField(max_length=250,blank=True, null=True,  help_text='사람 이름을 기입하되 ,로 구분 space 없도록')
    적용일 = models.DateTimeField ( blank=True, null=True )
    
    def __str__(self):
        return str(self.대표_보고명)

def user_directory_path(instance, filename):
    yesterday = (timezone.now()-timedelta(1))
    ex_yesterday = (timezone.now()-timedelta(2))
    
    while 휴일_DB.objects.filter(Q(휴일=yesterday)) :
        yesterday = yesterday - timedelta(1)
        ex_yesterday = ex_yesterday - timedelta(1)
        
    while 휴일_DB.objects.filter(Q(휴일=ex_yesterday)) :
        ex_yesterday = ex_yesterday - timedelta(1)
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    return ( '일일보고/전기사용량/' + str(ex_yesterday.date()) +'/'+ filename) 

class 전기사용량_DB(models.Model):
    # 보고일 = models.DateField(default=date.today) 
    # 등록자_fk = models.ForeignKey(개인_INFO, on_delete=models.CASCADE,default=1,db_column='등록자_id' )
    id = models.AutoField(primary_key=True)
    등록자 = models.CharField(max_length=15,blank=True, null=True)
    하이전기_file = models.FileField(upload_to=user_directory_path, max_length=254, default='')
    폴리전기_file = models.FileField(upload_to=user_directory_path, max_length=254, default='')
    일자 = models.DateField(default=(timezone.now().date()-timedelta(days=1)))  
    published_date = models.DateTimeField ( default=timezone.now )
    


class 조직_INFO(models.Model): 
###     https://stackoverflow.com/questions/58072651/how-to-set-initial-value-of-primary-key-in-django
###     python manage.py makemigrations 전사일일업무 --empty
    조직이름 = models.CharField(max_length=30, primary_key=True , default=unique_id, help_text='primary key 입니다.')
    보고순서= models.IntegerField( blank=True, null=True, default=0, unique=True, help_text='unique 정수 5자리 입니다. ')
    is_이슈보고 = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    상급조직_1차 = models.CharField(max_length=30,blank=True, null=True) 
    상급조직_2차 = models.CharField(max_length=30,blank=True, null=True) 
    대표_보고명  = models.CharField(max_length=30,blank=True, null=True)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.조직이름

class 개인_INFO(models.Model): 
    user_fk   = models.ForeignKey (settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_fk')
    보고순서= models.IntegerField( blank=True, null=True, default=0, unique=True, help_text='unique 정수 5자리 입니다. ')
    is_전기사용 = models.BooleanField(default=False)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.user_fk.user_성명

class ISSUE_리스트_DB(models.Model):
#   https://stackoverflow.com/questions/12188142/set-minimum-value-for-a-datetimefield    
    def clean(self, *args, **kwargs):
            # run the base validation
        super(ISSUE_리스트_DB, self).clean(*args, **kwargs)

        # Don't allow dates older than now.
        요일_list = ['(월)','(화)','(수)','(목)','(금)','(토)','(일)' ]
        today = timezone.now()
        yesterday = (timezone.now()-timedelta(1))
        ex_yesterday = (timezone.now()-timedelta(2))
        
        while 휴일_DB.objects.filter( 휴일 =yesterday) :
            yesterday = yesterday - timedelta(1)
            ex_yesterday = ex_yesterday - timedelta(1) 
        if self.일자 < yesterday.date() :
            raise ValidationError(f'일자는 {yesterday.date()} 이전은 입력할 수 없습니다.')

    조직이름_id = models.ForeignKey(조직_INFO, on_delete=models.CASCADE, db_column='조직이름_id',default='admin')
    일자 = models.DateField(default=date.today) 
    활동현황 = models.TextField ( default='')
    세부내용 = models.TextField ( blank=True, null=True, default='')
    완료예정일 = models.DateField(blank=True, null=True) 
    진척율 = models.CharField(max_length=10, blank=True, null=True, default='')
    유관부서 = models.CharField(max_length=25, blank=True, null=True, default='')
    비고 = models.TextField ( blank=True, null=True, default='')
    #전기사용량_fk = models.ForeignKey(전기사용량_DB, on_delete=models.CASCADE, blank=True, null=True, default=1,  db_column='전기사용량_fk')
    # 하이전기_file = models.FileField(upload_to=user_directory_path, max_length=254, default='')
    # 폴리전기_file = models.FileField(upload_to=user_directory_path, max_length=254, default='')
    
    등록자_id = models.ForeignKey(개인_INFO, on_delete=models.CASCADE, db_column='등록자_id',default=88)
    등록일 = models.DateTimeField( default=timezone.now)
    등록_weekno = models.IntegerField( blank=True, null=True, default=timezone.now().isocalendar().week  )  ### old version isocalendar()[1]
    등록_month  = models.IntegerField( blank=True, null=True, default=timezone.now().date().month)
    등록_year   = models.IntegerField( blank=True, null=True, default=timezone.now().date().year)
 
    대표_보고명 = models.CharField(max_length=15,blank=True, null=True)
    대표_보고순서   = models.IntegerField( blank=True, null=True, default=0,  help_text='unique 정수 5자리 입니다. ')
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()
        
    def save(self, *args, **kwargs):
        # super(ISSUE_리스트_DB, self).save(*args, **kwargs)

        self.등록_weekno = timezone.now().isocalendar().week
        self.등록_month = timezone.now().date().month
        self.등록_year = timezone.now().date().year
        self.등록일 = timezone.now()
        super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.조직이름_id)
    

class 개인_리스트_DB(models.Model): 
#    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    조직이름_id = models.ForeignKey(조직_INFO, on_delete=models.CASCADE,default='', db_column='조직이름_id')
    일자 = models.DateField(default=date.today) 
    업무내용 = models.TextField ( default='')
    업무주기 = models.CharField(max_length=10,blank=True, null=True)
    소요시간 = models.FloatField (blank=True, null=True, default=0)
    주요산출물=models.TextField ( blank=True, null=True, default='')
    비고 = models.TextField ( blank=True, null=True, default='')
    # 직책 = models.CharField(max_length=10,blank=True, null=True)
    # 직책명=models.CharField(max_length=10,blank=True, null=True)
    # 보고순서= models.IntegerField( blank=True, null=True, default=0)
    
    # 상급조직_1차 = models.CharField(max_length=30,blank=True, null=True) 
    # 상급조직_2차 = models.CharField(max_length=30,blank=True, null=True) 
    
    등록자_id = models.ForeignKey(개인_INFO, on_delete=models.CASCADE,default=1,db_column='등록자_id' )
    등록일 = models.DateTimeField( default=timezone.now)
    등록_weekno = models.IntegerField( blank=True, null=True, default=timezone.now().isocalendar().week)
    등록_month  = models.IntegerField( blank=True, null=True, default=timezone.now().date().month)
    등록_year   = models.IntegerField( blank=True, null=True, default=timezone.now().date().year)    

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.등록자_id.user_fk.user_성명
    
    def save(self, *args, **kwargs):
        # super(개인_리스트_DB, self).save(*args, **kwargs)
        #model_obj = self.get_object()
        self.등록_weekno = timezone.now().isocalendar().week
        self.등록_month = timezone.now().date().month
        self.등록_year = timezone.now().date().year
        self.등록일 = timezone.now()
        super(개인_리스트_DB, self).save(*args, **kwargs)


    
class 휴일_DB(models.Model): 
    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    휴일 = models.DateField(default=date.today, unique=True) 
    휴일내용 = models.CharField(max_length=25,blank=True, null=True)

    def __str__(self):
        return str(self.휴일)
    
class ISSUE_보고현황(models.Model): 
    id = models.BigAutoField(primary_key=True)
    # 조직이름_id = models.ForeignKey (조직_INFO, on_delete=models.CASCADE,blank=True, null=True,default='', db_column='조직이름_id')
    대표_보고명 = models.CharField(max_length=15,blank=True, null=True)
    대표_보고순서 = models.IntegerField( blank=True, null=True, default=0,  help_text='unique 정수 5자리 입니다. ')
    
    보고일 = models.DateField(default=date.today) 
    보고건수 = models.IntegerField( blank=True, null=True, default=0)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.조직이름_id
    
class 개인_보고현황(models.Model): 
    id = models.BigAutoField(primary_key=True)
    등록자_id = models.ForeignKey (개인_INFO, on_delete=models.CASCADE,blank=True, null=True,default='', db_column='등록자_id')
    조직이름_id = models.ForeignKey (조직_INFO, on_delete=models.CASCADE,blank=True, null=True,default='', db_column='조직이름_id')
    보고일 = models.DateField(default=date.today) 
    보고건수 = models.IntegerField( blank=True, null=True, default=0)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.등록자_id)
    
# class 기타_INFO(models.Model): 
#     id = models.BigAutoField(primary_key=True)
#     구분 = models.CharField(max_length=25,blank=True, null=True)
#     설정값 = models.TimeField(blank=True, null=True, help_text="시간 field 입니다.") 
#     설정값_1 = ColorField(default='#FF0000' , help_text="character field로, 당일 업무에 대한 배경색 입니다.") #)models.CharField(max_length=10, blank=True, null=True
    

#     def publish(self):
#         self.published_date = timezone.now()
#         self.save()

#     def __str__(self):
#         return self.구분
        
