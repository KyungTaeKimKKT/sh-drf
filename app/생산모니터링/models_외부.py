from ipaddress import ip_address
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import 휴식시간_DB
import pytz

import util.utils_func as Utils
from websocket import create_connection

class 생산계획실적(models.Model):
    id = models.AutoField ( primary_key=True )
    sensor_id = models.CharField(max_length=10, blank=True, null=True, default='')
    line_no = models.CharField(max_length=20, blank=True, null=True, default='')
    start_time = models.DateTimeField( default=timezone.now)
    end_time = models.DateTimeField( default=timezone.now)
    plan_qty    = models.IntegerField ( blank=True, null=True, default=0)
    job_qty     = models.IntegerField ( blank=True, null=True, default=0)
    oper_yn = models.CharField(max_length=2, blank=True, null=True, default='')
    생성시간    = models.DateTimeField( default=timezone.now)
    등록자    = models.CharField(max_length=15, blank=True, null=True, default='')
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField (default=True )
    job_qty_time    = models.DateTimeField( default=timezone.now)
    생산capa = models.IntegerField(default=0)
 
    class Meta:
        managed = False
        db_table = 'iot\".\"생산계획실적'

    def save(self, *args, **kwargs):
        # self.생산capa = self.get_생산capa()
        self.생성시간 = timezone.now()
        super(생산계획실적, self).save(*args, **kwargs) 

    def get_생산capa(self):
        obj_sensor_기준정보 = sensor_기준정보.objects.using('생산모니터링').get(sensor_id__contains = self.sensor_id )
        총가동시간 =self.capa_분석( now= False )
        이론생산량 = 총가동시간 / obj_sensor_기준정보.tact_time if 총가동시간 else 0
        return int(이론생산량)
    
    #  now가 False 이면 생산계획상 종료시간, 
    def capa_분석( self, now ):
        start_time = self.start_time.time()
        end_time  = self.end_time.time() if not now else now.time()

        시작시간 = self.start_time
        종료시간 = self.end_time if not now else now

        총가동시간 = 0
        
        qs = 휴식시간_DB.objects.filter(적용대상__icontains = self.sensor_id).filter( 휴식시간_시작__gte = start_time , 휴식시간_종료__lte = end_time).order_by("휴식시간_시작")
        휴식시간_count = 0
        휴식시간_list = []

        utc=pytz.UTC
        for obj in qs:
            휴식시간_시작 = datetime.combine(date.today(),obj.휴식시간_시작)
            휴식시간_종료 = datetime.combine(date.today(),obj.휴식시간_종료)

# https://stackoverflow.com/questions/15307623/cant-compare-naive-and-aware-datetime-now-challenge-datetime-end
            휴식시간_시작 = utc.localize(휴식시간_시작) 
            휴식시간_종료 = utc.localize(휴식시간_종료) 

            휴식시간_list.append ( ( 휴식시간_종료-휴식시간_시작).total_seconds() )
            if 종료시간 > 휴식시간_시작 :
                if 종료시간 < 휴식시간_종료:
                    종료시간 = 휴식시간_시작
                else:
                    휴식시간_count += 1
        # print ( 휴식시간_list , sum (휴식시간_list[:1]), sum (휴식시간_list[:2]), sum (휴식시간_list[:3]), sum (휴식시간_list[:4]), sum (휴식시간_list))      
        if 휴식시간_count == 0: #10시 대 이전
            총가동시간 = (종료시간-시작시간).total_seconds()
        elif 휴식시간_count == 1:   #점심 대 이전
            총가동시간 =  (종료시간-시작시간).total_seconds() - sum (휴식시간_list[:1])
        elif 휴식시간_count == 2:   #3시 대 이전
            총가동시간 =  (종료시간-시작시간).total_seconds() - sum (휴식시간_list[:2])
        elif 휴식시간_count == 3:   #저녁 대 이전
            총가동시간 =  (종료시간-시작시간).total_seconds() - sum (휴식시간_list[:3])
        elif 휴식시간_count == 4:   #저녁 8시 이전
            총가동시간 = (종료시간-시작시간).total_seconds() - sum (휴식시간_list[:4])
        else :                      #휴식시간_count == 5:   #저녁 8시 이후
            총가동시간 =  (종료시간-시작시간).total_seconds() - sum (휴식시간_list)
        
        # if 'S-06' in obj_생산계획.sensor_id:
        #     print ( obj_생산계획.sensor_id, now, 휴식시간_count, 총가동시간)
        return 총가동시간               

@receiver(models.signals.post_save, sender=생산계획실적)
def 생산계획실적_post_save_receiver(sender, instance, **kwargs):
    print ( 'signal dispatcher : post_save', sender, instance )
    URL_WS = "ws://mes.swgroup.co.kr:9998/broadcast/db_monitor/"
    msg = {
            "type":"broadcast",
            "sender":"system",
            "message": f"{str(instance.id)} saving message",
            "send_time" :  datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
    Utils.send_WS_msg_short( instance, url= URL_WS, msg=msg)
    # ws = create_connection("ws://mes.swgroup.co.kr:9998/broadcast/db_monitor/")
    # ws.send (  json.dumps(  
    #             {
    #                 "type":"broadcast",
    #                 "sender":"system",
    #                 "message": f"{str(instance.id)} saving message",
    #                 "send_time" :  datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    #             }, ensure_ascii=False
    #             ) 
    #         ) 




class NEW_SENSOR_생산_MASTER(models.Model):
    id = models.AutoField ( primary_key=True )
    server_time = models.DateTimeField( default=timezone.now)
    rpi_time = models.DateTimeField( default=timezone.now)
    sensor_id = models.CharField(max_length=10,  default='')
    s1 = models.BooleanField(default=True, help_text="0: 미인식, 1:인식")
    s2 = models.BooleanField(default=True, help_text="0: 미인식, 1:인식")
    생산수량 = models.IntegerField (  default=0)
    sensor_mode = models.CharField(max_length=10,  default='')
    판정_max  = models.FloatField (  default=0)
    판정_min   = models.FloatField (  default=0)
 
    class Meta:
        managed = False
        db_table = 'iot\".\"sensor_생산_master'
        
        
class sensor(models.Model):
    id = models.IntegerField ( primary_key=True )
    crt_time = models.DateTimeField( default=timezone.now)
    rd_time = models.DateTimeField( default=timezone.now)
    cpu_temp  = models.FloatField ( blank=True, null=True, default='')
    cpu_util  = models.FloatField ( blank=True, null=True, default='')
    mem_free  = models.FloatField ( blank=True, null=True, default='')
    mem_total = models.FloatField ( blank=True, null=True, default='')
    disk_free = models.FloatField ( blank=True, null=True, default='')
    disk_total = models.FloatField ( blank=True, null=True, default='')
    sensor_id = models.CharField(max_length=10, blank=True, null=True, default='')
    sensor_type = models.CharField(max_length=10, blank=True, null=True, default='')
    tag = models.CharField(max_length=10, blank=True, null=True, default='')
    value1 = models.IntegerField ( blank=True, null=True, default=0)
    value2 = models.IntegerField ( blank=True, null=True, default=0)
    value3 = models.IntegerField ( blank=True, null=True, default=0)
    job_qty = models.IntegerField ( blank=True, null=True, default=0)
        
    class Meta:
        managed = False
        db_table = 'shinwoo\".\"sensor'
        
    # def publish(self):
    #     self.published_date = timezone.now()
    #     self.save()
        
    # def save(self, *args, **kwargs):
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    #     self.등록_weekno = timezone.now().isocalendar()[1]
    #     self.등록_month = timezone.now().date().month
    #     self.등록_year = timezone.now().date().year
    #     self.등록일 = timezone.now()
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    # def __str__(self):
    #     return str(self.sensor_id)
    
class sensor_기준정보(models.Model):
    id = models.AutoField ( primary_key=True )
    sensor_id = models.CharField(max_length=10, blank=True, null=True, default='')
    sensor_name = models.CharField(max_length=20, blank=True, null=True, default='')
    sensor_설명  = models.CharField(max_length=50, blank=True, null=True, default='')
    ip_주소  =models.CharField(max_length=20, blank=True, null=True, default='')
    is_active  = models.BooleanField(default=True, help_text="0: 미인식, 1:인식")
    tact_time = models.IntegerField ( blank=True, null=True, default=90)
    duration    = models.IntegerField ( blank=True, null=True, default=3)
    prevent     = models.IntegerField ( blank=True, null=True, default=0)
    task_yellow = models.IntegerField ( blank=True, null=True, default=5)
    task_red    = models.IntegerField ( blank=True, null=True, default=5)
    mode = models.CharField(max_length=10, blank=True, null=True, default='')
    sensor_수량    = models.IntegerField ( blank=True, null=True, default=2)
    생성시간    = models.DateTimeField( default=timezone.now)
    수정시간   = models.DateTimeField( default=timezone.now)
    line_no = models.CharField(max_length=20, blank=True, null=True, default='')
    alarm_yellow    = models.IntegerField ( blank=True, null=True, default=5)
    alarm_red    = models.IntegerField ( blank=True, null=True, default=5)
    # status_time    = models.IntegerField ( blank=True, null=True, default=0)
     
    class Meta():
        managed = False
        db_table = 'iot\".\"sensor_기준정보'
        
    # def publish(self):
    #     self.published_date = timezone.now()
    #     self.save()
        
    # def save(self, *args, **kwargs):
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    #     self.등록_weekno = timezone.now().isocalendar()[1]
    #     self.등록_month = timezone.now().date().month
    #     self.등록_year = timezone.now().date().year
    #     self.등록일 = timezone.now()
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.sensor_id )
    
    
class order(models.Model):
    id = models.IntegerField ( primary_key=True )
    sensor_id = models.CharField(max_length=10, blank=True, null=True, default='')
    line_no = models.CharField(max_length=20, blank=True, null=True, default='')
    start_time = models.DateTimeField( default=timezone.now)
    end_time = models.DateTimeField( default=timezone.now)
    plan_qty    = models.IntegerField ( blank=True, null=True, default=0)
    job_qty     = models.IntegerField ( blank=True, null=True, default=0)
    oper_yn = models.CharField(max_length=2, blank=True, null=True, default='')
    crt_date    = models.DateTimeField( default=timezone.now)
    mod_date    = models.DateTimeField( default=timezone.now)
 
    class Meta():
        managed = False
        db_table = 'shinwoo\".\"order'
        
    # def publish(self):
    #     self.published_date = timezone.now()
    #     self.save()
        
    # def save(self, *args, **kwargs):
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    #     self.등록_weekno = timezone.now().isocalendar()[1]
    #     self.등록_month = timezone.now().date().month
    #     self.등록_year = timezone.now().date().year
    #     self.등록일 = timezone.now()
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.sensor_id )
    
class test_server(models.Model):
    id = models.AutoField ( primary_key=True )
    title= models.CharField(max_length=255, blank=True, null=True, default='')
    context = models.TextField(blank=True, null=True, default='')
    서버시간    = models.DateTimeField( default=timezone.now)
 
    class Meta():
        managed = False
        db_table = 'public\".\"temp'
        
    # def publish(self):
    #     self.published_date = timezone.now()
    #     self.save()
        
    # def save(self, *args, **kwargs):
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    #     self.등록_weekno = timezone.now().isocalendar()[1]
    #     self.등록_month = timezone.now().date().month
    #     self.등록_year = timezone.now().date().year
    #     self.등록일 = timezone.now()
    #     super(ISSUE_리스트_DB, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.title )