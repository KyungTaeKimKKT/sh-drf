from django.conf import settings
from django.db import models
from django.utils import timezone

class 출하현장_master_DB(models.Model):
    매출_month  = models.IntegerField( blank=True, null=True, default=0)
    매출_year   = models.IntegerField( blank=True, null=True, default=0)
    현장명 = models.CharField(max_length=50, blank=True, null=True, default='')
    고객사 = models.CharField(max_length=15, blank=True, null=True, default='')
    구분 = models.CharField(max_length=10, blank=True, null=True, default='')
    부서 = models.CharField(max_length=15, blank=True, null=True, default='')
    담당자 = models.CharField(max_length=15, blank=True, null=True, default='')
    기여도 = models.CharField(max_length=5, blank=True, null=True, default='')
    비고 = models.CharField(max_length=25, blank=True, null=True, default='')
    check_admin = models.BooleanField(default=False)
    금액 = models.BigIntegerField (blank=True, null=True, default=0 )
    id_made = models.CharField(max_length=200,  null=True, blank=True, default=None)
        
    등록자 = models.CharField(max_length=15, blank=True, null=True,default='')    
    등록일 = models.DateTimeField( blank=True, null=True, default=timezone.now)
    등록_weekno = models.IntegerField( blank=True, null=True, default=0)

    설정_fk = models.ForeignKey("영업mbo_설정DB", on_delete=models.CASCADE, blank=True, null=True)
 
    def __str__(self):
        return self.현장명
    
class Temp_출하현장_master_DB(models.Model):
    매출_month  = models.IntegerField( blank=True, null=True, default=0)
    매출_year   = models.IntegerField( blank=True, null=True, default=0)
    현장명 = models.CharField(max_length=50, blank=True, null=True, default='')
    고객사 = models.CharField(max_length=15, blank=True, null=True, default='')
    구분 = models.CharField(max_length=10, blank=True, null=True, default='')
    부서 = models.CharField(max_length=15, blank=True, null=True, default='')
    담당자 = models.CharField(max_length=15, blank=True, null=True, default='')
    기여도 = models.CharField(max_length=5, blank=True, null=True, default='')
    비고 = models.CharField(max_length=25, blank=True, null=True, default='')
    check_admin = models.BooleanField(default=False)
    금액 = models.BigIntegerField (blank=True, null=True, default=0 )
    id_made = models.CharField(max_length=200,  null=True, blank=True, default=None)
        
    등록자 = models.CharField(max_length=15, blank=True, null=True,default='')    
    등록일 = models.DateTimeField( blank=True, null=True, default=timezone.now)
    등록_weekno = models.IntegerField( blank=True, null=True, default=0)

    설정_fk = models.ForeignKey("영업mbo_설정DB", on_delete=models.CASCADE, blank=True, null=True)
 
    def __str__(self):
        return self.현장명
    
class 사용자등록_DB (models.Model):
    신규현장_fk = models.ForeignKey("신규현장_등록_DB", on_delete=models.CASCADE, blank=True, null=True)
    고객사 = models.CharField(max_length=15, blank=True, null=True, default='')
    구분 = models.CharField(max_length=10, blank=True, null=True, default='')
    기여도 = models.CharField(max_length=5, blank=True, null=True, default='')
    비고 = models.CharField(max_length=25, blank=True, null=True, default='')
    등록자 = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True )
    등록자_snapshot = models.CharField(max_length=15, blank=True, null=True, default='')
    is_선택 = models.BooleanField( default=False )
    by_admin = models.BooleanField( default=False )
    # is_관리자마감 = models.BooleanField( default=False )

class 신규현장_등록_DB ( models.Model ):
    설정_fk = models.ForeignKey("영업mbo_설정DB", on_delete=models.CASCADE, blank=True, null=True)
    매출_month  = models.IntegerField( blank=True, null=True, default=0)
    매출_year   = models.IntegerField( blank=True, null=True, default=0)
    현장명 = models.CharField(max_length=50, blank=True, null=True, default='')
    
    sales_input_fks = models.ManyToManyField(사용자등록_DB , null=True, blank=True , related_name='sales_input')
    admin_input_fk = models.ForeignKey ( 사용자등록_DB, models.DO_NOTHING, null=True, blank=True , related_name='admin_input')

    check_admin = models.BooleanField(default=False)
    금액 = models.BigIntegerField (blank=True, null=True, default=0 )
    id_made = models.CharField(max_length=200,  null=True, blank=True, default=None)

    is_관리자마감 = models.BooleanField(default=False)



# class 개인별_DB(models.Model):
#     신규현장_fk = models.ForeignKey("신규현장_등록_DB", on_delete=models.CASCADE, blank=True, null=True)

#     고객사 = models.CharField(max_length=15, blank=True, null=True, default='')
#     구분 = models.CharField(max_length=10, blank=True, null=True, default='')
#     부서 = models.CharField(max_length=15, blank=True, null=True, default='')
#     담당자 = models.CharField(max_length=15, blank=True, null=True, default='')
#     기여도 = models.CharField(max_length=5, blank=True, null=True, default='')
#     비고 = models.CharField(max_length=100, blank=True, null=True, default='')
#     check_admin = models.BooleanField(default=False)
  
#     담당자_fk = models.ForeignKey( 
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.SET_NULL, 
#         blank=True, 
#         null=True 
#     )
#     등록일 = models.DateTimeField( default=timezone.now)
 

class 관리자등록_DB(models.Model):
    신규현장_fk = models.ForeignKey("신규현장_등록_DB", on_delete=models.CASCADE, blank=True, null=True)
    고객사 = models.CharField(max_length=15, blank=True, null=True, default='')
    구분 = models.CharField(max_length=10, blank=True, null=True, default='')
    부서 = models.CharField(max_length=15, blank=True, null=True, default='')
    담당자 = models.CharField(max_length=15, blank=True, null=True, default='')
    담당자_fk = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True )
    기여도 = models.CharField(max_length=5, blank=True, null=True, default='')
    비고 = models.CharField(max_length=100, blank=True, null=True, default='')
    check_admin = models.BooleanField(default=False)
    # 금액 = models.BigIntegerField (blank=True, null=True, default=0 )
    # id_made = models.CharField(max_length=200,  null=True, blank=True, default=None)
    
    # 검증결과 = models.CharField(max_length=15, blank=True, null=True, default='')
    등록자 = models.CharField(max_length=15, default='')    
    등록일 = models.DateTimeField( default=timezone.now)
    # 등록_weekno = models.IntegerField( blank=True, null=True, default=0)

    is_선택 = models.BooleanField( default=False )
 

   
def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    #print ("\n",user_{0}/{1}'.format(instance.user.username, filename),  )
    return ( '영업mbo/매출/' + str(instance.매출_year) +'-'+str(instance.매출_month) +'/'+ filename) 

class 영업mbo_설정DB(models.Model):

    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    매출_month  = models.IntegerField( default=timezone.now().month -1)
    매출_year   = models.IntegerField( default=timezone.now().year)
    # file_제목 = models.CharField(max_length=254, blank=True, null=True)
    file = models.FileField(upload_to=user_directory_path, max_length=254, blank=True, null=True)
    id_made = models.CharField (max_length=15, unique=True, default=str(timezone.now))
    is_시작 = models.BooleanField(default=False)
    is_완료 = models.BooleanField(default=False)
    
    현재_입력자 = models.CharField(max_length=254, blank=True, null=True)
    
    모든현장_금액_sum = models.BigIntegerField (blank=True, null=True, default=0 )
    신규현장_금액_sum = models.BigIntegerField (blank=True, null=True, default=0 )
    기존현장_금액_sum = models.BigIntegerField (blank=True, null=True, default=0 )
    
    모든현장_count = models.IntegerField( blank=True, null=True, default=0 )
    기존현장_count = models.IntegerField( blank=True, null=True, default=0 )
    신규현장_count = models.IntegerField( blank=True, null=True, default=0 )
    
    is_검증 = models.BooleanField(default=False)
    is_master적용 = models.BooleanField(default=False)
    is_개인별할당 = models.BooleanField(default=False)
    is_관리자마감 = models.BooleanField(default=True)
            
    등록자 = models.CharField(max_length=15, default='')    
    등록일 = models.DateTimeField( default=timezone.now)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.매출_year)
    
    def save(self, *args, **kwargs):
        # self.id_made = str(self.매출_year)+'-'+str(self.매출_month)
        super(영업mbo_설정DB, self).save(*args, **kwargs)



class 영업mbo_엑셀등록(models.Model):

    매출_year   = models.IntegerField( blank=True, null=True, default=timezone.now().year)
    매출_month  = models.IntegerField( blank=True, null=True, default=timezone.now().month -1)

    현장명 = models.CharField(max_length=50, blank=True, null=True, default='')
    금액 = models.BigIntegerField (blank=True, null=True, default=0 )
        
    등록자 = models.CharField(max_length=15, default='')    
    등록일 = models.DateTimeField( default=timezone.now)
    id_made = models.CharField(max_length=200,  null=True, blank=True, default=None)
    is_exist= models.BooleanField(default=False)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.현장명
    
class 고객사_DB(models.Model):
    고객사_id     = models.CharField(max_length=20, default='')    
    고객사_표시명 =  models.CharField(max_length=20, default='') 
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.고객사_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 구분_DB(models.Model):
    구분_id     = models.CharField(max_length=20, default='')    
    구분_표시명 =  models.CharField(max_length=20, default='') 
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.구분_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 기여도_DB(models.Model):
    기여도_id     = models.CharField(max_length=20, default='')    
    기여도_표시명 =  models.CharField(max_length=20, default='') 
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.기여도_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
    
class 사용자_DB(models.Model):
    사용자_id     = models.CharField(max_length=20, default='')    
    사용자_표시명 =  models.CharField(max_length=20, default='') 
    부서 = models.CharField(max_length=20, default='') 
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.사용자_id #, self.고객사_표시명, self.is_영업디자인, self.is_MBO

class 년간보고_지사_고객사(models.Model):
    매출년도 = models.IntegerField( blank=True, null=True, default=timezone.now().year)   
    부서 = models.CharField(max_length=20, default='')    
    고객사 = models.CharField(max_length=20, default='') # elevator 사
    분류 = models.CharField(max_length=10, default='') # 계획, 실적 등
      
    month_01 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_02 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_03 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_04 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_05 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_06 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_07 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_08 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_09 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_10 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_11 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_12 = models.BigIntegerField (blank=True, null=True, default=0 )
    합계 = models.BigIntegerField (blank=True, null=True, default=0 )
    지사_보고순서 = models.BigIntegerField (blank=True, null=True, default=0 )    
 
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.부서) #, self.고객사_표시명, self.is_영업디자인, self.is_MBO


class 년간보고_지사_구분(models.Model):
    매출년도 = models.IntegerField( blank=True, null=True, default=timezone.now().year)   
    부서 = models.CharField(max_length=20, default='')    
    구분 = models.CharField(max_length=20, default='') # ne, mode 등
    분류 = models.CharField(max_length=10, default='') # 계획, 실적 등
      
    month_01 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_02 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_03 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_04 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_05 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_06 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_07 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_08 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_09 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_10 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_11 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_12 = models.BigIntegerField (blank=True, null=True, default=0 )
    합계 = models.BigIntegerField (blank=True, null=True, default=0 )
    지사_보고순서 = models.BigIntegerField (blank=True, null=True, default=0 )    
 
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.부서) #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
       
#   https://stackoverflow.com/questions/61226186/how-can-i-add-two-different-integer-fields-of-the-same-model-in-django    
    def save(self, *args, **kwargs):
        #if not self.구분 == 'TOTAL':
            if not self.분류 == '달성률':
                try:
                    self.합계 = self.month_01 +self.month_02 + self.month_03+ self.month_04+ self.month_05+ self.month_06+ self.month_07+ self.month_08+ self.month_09+ self.month_10 + self.month_11 + self.month_12
                    # obj = 보고기준_DB.objects.filter(대분류='지사').filter(부서=self.부서).filter(구분=self.구분).filter(분류=self.분류)[0]
                    # self.지사_보고순서 = obj.지사_보고순서
                    # print ( self.부서,self.구분, self.분류, self.지사_보고순서 )
                    super().save(*args, **kwargs)
                except Exception as e:
                    print ( self, 'ERROR:', e)
                    super().save(*args, **kwargs)
            else:
                try:
                    super().save(*args, **kwargs)
                except:
                    pass
   

                
    #        self.지사_보고순서 = 보고기준_DB.objects.filter(부서=self.부서).values("지사_보고순서")[0]    
            # super(년간보고_지사_구분, self).save(*args, **kwargs)
            # super().save(*args, **kwargs)
        
# class 상속 : https://dgkim5360.tistory.com/entry/django-model-inheritance
class 년간보고_개인별 (models.Model):
    담당자 = models.CharField(max_length=20, default='')  
    당월누적 = models.BigIntegerField (blank=True, null=True, default=0 )
    
    매출년도 = models.IntegerField( blank=True, null=True, default=timezone.now().year)   
    부서 = models.CharField(max_length=20, default='')    
    구분 = models.CharField(max_length=20, default='') # ne, mode 등
    분류 = models.CharField(max_length=10, default='') # 계획, 실적 등
      
    month_01 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_02 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_03 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_04 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_05 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_06 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_07 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_08 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_09 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_10 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_11 = models.BigIntegerField (blank=True, null=True, default=0 )
    month_12 = models.BigIntegerField (blank=True, null=True, default=0 )
    합계 = models.BigIntegerField (blank=True, null=True, default=0 )
    개인_보고순서 = models.BigIntegerField (blank=True, null=True, default=0 )
 
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.부서) #, self.고객사_표시명, self.is_영업디자인, self.is_MBO
#   https://stackoverflow.com/questions/61226186/how-can-i-add-two-different-integer-fields-of-the-same-model-in-django    
    def save(self, *args, **kwargs):
        if self.분류 == '계획' or  self.분류 == '실적':
            self.합계 = self.month_01 +self.month_02
            self.합계 = self.합계 + self.month_03
            self.합계 = self.합계 + self.month_04
            self.합계 = self.합계 + self.month_05
            self.합계 = self.합계 + self.month_06
            self.합계 = self.합계 + self.month_07
            self.합계 = self.합계 + self.month_08
            self.합계 = self.합계 + self.month_09
            self.합계 = self.합계 + self.month_10
            self.합계 = self.합계 + self.month_11
            self.합계 = self.합계 + self.month_12
            # try:
            #     self.개인_보고순서 = 보고기준_DB.objects.filter(담당자=self.담당자).filter(구분=self.구분).filter(분류=self.분류).values_list("개인_보고순서",flat=True)[0]
            # except:
            #     self.개인_보고순서 = 0
            # print ( "self.개인_보고순서: ",self.담당자,self.구분, self.분류,  self.개인_보고순서)
        #self.지사_보고순서 = 보고기준_DB.objects.filter(부서=self.부서).filter(구분=self.구분).filter(분류=self.분류).values_list("지사_보고순서",flat=True)
        else:
            pass
        
        super(년간보고_개인별, self).save(*args, **kwargs)
        
class 년간보고_달성률_기준 (models.Model):
    # 달성률_low <=  달성률 < 달성률_high
    달성률_low = models.IntegerField( blank=True, null=True, default=0, help_text='2자리 숫자로 입력하세요')
    달성률_high = models.IntegerField( blank=True, null=True, default=0, help_text='2자리 숫자로 입력하세요')     
    폰트색 = models.CharField(max_length=20, default='black')  
    배경색   = models.CharField(max_length=20, default='white') 
 
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.달성률_low) #, self.고객사_표시명, self.is_영업디자인, self.is_MBO


class 보고기준_DB(models.Model):
    대분류 = models.CharField(max_length=10, default='',help_text='지사, 개인 으로 입력하세요') # 지사, 개인
    담당자 = models.CharField(max_length=20, blank=True, null=True,default='')    
    #사용자_표시명 =  models.CharField(max_length=20, default='') 
    부서 = models.CharField(max_length=20,blank=True, null=True, default='')    
    구분 = models.CharField(max_length=20,blank=True, null=True, default='', help_text='NE, MOD, 비정규 으로 입력하세요') # ne, mode 등
    분류 = models.CharField(max_length=10,blank=True, null=True, default='', help_text='계획, 실적 으로 입력하세요') # 계획, 실적 등
    is_지사보고 = models.BooleanField(default=False)
    is_개인보고 = models.BooleanField(default=False)
    지사_보고순서 = models.BigIntegerField (blank=True, null=True, default=0 , help_text='5자리 숫자로 입력하세요')
    개인_보고순서 = models.BigIntegerField (blank=True, null=True, default=0 , help_text='5자리 숫자로 입력하세요')
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.대분류 #, self.고객사_표시명, self.is_영업디자인, self.is_MBO