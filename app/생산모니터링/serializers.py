"""
Serializers for 생산모니터링
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault

from rest_framework.authtoken.models import Token

from datetime import datetime,date,time, timezone
import datetime as dt
import time

from 생산모니터링.models_외부 import (
    sensor, 
    sensor_기준정보, 
    order, 
    test_server, 
    NEW_SENSOR_생산_MASTER, 
    생산계획실적
)

from 생산모니터링.models import (
    무재해_DB, 
    생산계획_사용자_DB, 
    SENSOR_NETWORK_DB,  
    휴식시간_DB
)

class 무재해_DB_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 무재해_DB
        fields = '__all__'
        read_only_fields = ['id']

class sensor_기준정보Serializer(serializers.ModelSerializer):
    # sensor_기준정보_queryset = sensor_기준정보.objects.using('생산모니터링').all()
    class Meta:
        model = sensor_기준정보
        # https://stackoverflow.com/questions/64476816/how-to-add-new-serializer-field-along-with-the-all-model-fields
        fields = [f.name for f in sensor_기준정보._meta.fields] 
        # fields = '__all__'
        read_only_fields = ['id']


class KIOSK_생산계획실적Serializer(serializers.ModelSerializer):
    sensor_기준정보_queryset = sensor_기준정보.objects.using('생산모니터링').all()
    휴식시간_queryset = 휴식시간_DB.objects.all()
    _운영tt = 0
    
    무재해 = serializers.SerializerMethodField()
    생산capa = serializers.SerializerMethodField()
    운영tt = serializers.SerializerMethodField()
    달성률 = serializers.SerializerMethodField()
    운영가동률 = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    TT = serializers.SerializerMethodField()
    
    # user_pks = TestUserDBSerializer(many=True, required=False )

    # https://stackoverflow.com/questions/69380007/how-to-get-current-user-id-in-django-rest-framework-serializer
    # current_user = serializers.SerializerMethodField('_get_current_user')
    # app사용자수 = serializers.SerializerMethodField('_get_app사용자수')
   
    class Meta:
        model = 생산계획실적
        # https://stackoverflow.com/questions/64476816/how-to-add-new-serializer-field-along-with-the-all-model-fields
        fields = [f.name for f in 생산계획실적._meta.fields] + ['운영tt' ,'달성률','운영가동률','status','생산capa','무재해', 'TT']
        # fields = '__all__'
        read_only_fields = ['id']

    def get_TT(self, obj):
        obj_sensor_기준정보 = self.sensor_기준정보_queryset.get(sensor_id__contains =  obj.sensor_id)
        return obj_sensor_기준정보.tact_time 

    def get_무재해(self,obj):
        무재해_instance = 무재해_DB.objects.filter(is_active=True).order_by('-무재해시작')[0]
        return 무재해_instance.무재해시작

    def get_status(self,obj):

        obj_sensor_기준정보 = self.sensor_기준정보_queryset.get(sensor_id__contains =  obj.sensor_id)
        now = datetime.now()
        if  not obj.plan_qty : return '생산계획없음'
        if ( obj.start_time > now): return '준비'
        elif ( obj.end_time < now): return '종료'
        
        if ( self.휴식시간_queryset.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__lte = now , 휴식시간_종료__gte = now).order_by("휴식시간_시작") ):
            if ( now <= datetime.combine(date.today(), dt.time(11,30)) ): return '휴식'
            elif ( now <= datetime.combine(date.today(), dt.time(14,00)) ): return '점심'
            elif ( now <= datetime.combine(date.today(), dt.time(17,00)) ): return '휴식'
            else : return '청소_저녁'
        if self._운영tt  <=  obj_sensor_기준정보.tact_time *2 : return '가동중'
        elif self._운영tt <= obj_sensor_기준정보.tact_time *5 : return '지연'
        else : return '정지'

    def get_운영가동률(self, obj):

        if not obj.plan_qty: return float(0)
        stime = time.time()
        obj_sensor_기준정보 = self.sensor_기준정보_queryset.get(sensor_id__contains =  obj.sensor_id)
        총가동시간 =self.capa_분석(obj, now= datetime.now() )
        이론생산량 = 총가동시간 / obj_sensor_기준정보.tact_time if 총가동시간 else 0
        return float("{:.1f}".format(obj.job_qty / 이론생산량 * 100)) if obj.plan_qty else obj.plan_qty

    def get_달성률(self, obj):
        return float("{:.1f}".format(obj.job_qty / obj.plan_qty * 100)) if obj.plan_qty else obj.plan_qty

    def get_운영tt(self, obj):

        tt_시작시간 = obj.start_time if ( obj.job_qty_time < obj.start_time) else  obj.job_qty_time
        운영tt = int( (datetime.now()-tt_시작시간).total_seconds() )
        self._운영tt = 운영tt
        return 운영tt
    
    def get_생산capa(self, obj):
        
        obj_sensor_기준정보 = sensor_기준정보.objects.using('생산모니터링').get(sensor_id__contains =  obj.sensor_id )
        총가동시간 =self.capa_분석(obj, now= False )
        이론생산량 = 총가동시간 / obj_sensor_기준정보.tact_time if 총가동시간 else 0
        return int(이론생산량)
    
    #  now가 False 이면 생산계획상 종료시간, 
    def capa_분석( self, obj, now ):
        start_time = obj.start_time.time()
        end_time  = obj.end_time.time() if not now else now.time()

        시작시간 = obj.start_time
        종료시간 = obj.end_time if not now else now

        총가동시간 = 0
        
        qs = self.휴식시간_queryset.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__gte = start_time , 휴식시간_종료__lte = end_time).order_by("휴식시간_시작")
        # qs = 휴식시간_DB.objects.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__gte = start_time , 휴식시간_종료__lte = end_time).order_by("휴식시간_시작")
        휴식시간_count = 0
        휴식시간_list = []
        for obj in qs:
            휴식시간_시작 = datetime.combine(date.today(),obj.휴식시간_시작)
            휴식시간_종료 = datetime.combine(date.today(),obj.휴식시간_종료)
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

     

    # def _get_current_user(self, instance):
    #     # user = Token.objects.get(key='token string').user
    #     # print (user)
    #     # user = self.context['request'].user.user_mailid
    #     return 'aaa'
    
    # def _get_app사용자수(self, instance):
    #     return instance.user_pks.all().count()

    # def _get_or_create_user_pks(self, user_pks, api_권한):
    #     for user_pk in user_pks:
    #         user_pk_obj, created = TestUserDB.objects.get_or_create(**user_pk)
    #         api_권한.user_pks.add(user_pk_obj)

    # def create(self, validated_data):
    #     user_pks = validated_data.pop('user_pks',[])
    #     api_권한 = Api_App권한.objects.create (**validated_data)
    #     self._get_or_create_user_pks(user_pks,api_권한)
    #     return api_권한
 
    # # https://stackoverflow.com/questions/50654337/django-writable-nested-serializers-update
    # def update(self, instance, validated_data):
    #     user_pks = validated_data.pop('user_pks')
    #     if user_pks is not None:
    #         instance.user_pks.clear()
    #         self._get_or_create_user_pks(user_pks, instance)
        
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)



class 생산계획Serializer(serializers.ModelSerializer):
    sensor_기준정보_queryset = sensor_기준정보.objects.using('생산모니터링').all()
    휴식시간_queryset = 휴식시간_DB.objects.all()

    
    생산capa = serializers.SerializerMethodField()

    class Meta:
        model = 생산계획실적        
        fields = ['id','line_no','생산capa', 'start_time','end_time','plan_qty','등록자']
        read_only_fields = ['id']

    def to_representation(self, instance: 생산계획실적  ):
        data = super().to_representation(instance)
        # data['start_time'] = instance.start_time.time()
        # data['end_time'] =instance.end_time.time()

        return data



    def get_생산capa(self, obj):
        obj_sensor_기준정보 = sensor_기준정보.objects.using('생산모니터링').get(sensor_id__contains =  obj.sensor_id )
        총가동시간 =self.capa_분석(obj, now= False )
        이론생산량 = 총가동시간 / obj_sensor_기준정보.tact_time if 총가동시간 else 0
        return int(이론생산량)
    
    #  now가 False 이면 생산계획상 종료시간, 
    def capa_분석( self, obj, now ):
        start_time = obj.start_time.time()
        end_time  = obj.end_time.time() if not now else now.time()

        시작시간 = obj.start_time
        종료시간 = obj.end_time if not now else now

        총가동시간 = 0
        
        qs = self.휴식시간_queryset.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__gte = start_time , 휴식시간_종료__lte = end_time).order_by("휴식시간_시작")
        # qs = 휴식시간_DB.objects.filter(적용대상__icontains = obj.sensor_id).filter( 휴식시간_시작__gte = start_time , 휴식시간_종료__lte = end_time).order_by("휴식시간_시작")
        휴식시간_count = 0
        휴식시간_list = []
        for obj in qs:
            휴식시간_시작 = datetime.combine(date.today(),obj.휴식시간_시작)
            휴식시간_종료 = datetime.combine(date.today(),obj.휴식시간_종료)
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

    def update(self, instance, validated_data):
        # print ( validated_data )

        # if user_pks is not None:
        #     instance.user_pks.set(user_pks )
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

            # if ( 'time' in attr ): setattr(instance, attr, self.utc_to_local(value) )
            # else: setattr(instance, attr, value)
        setattr( instance, '등록자', self._get_current_user().user_성명 )
        instance.save()
        return instance


    def utc_to_local(self,utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
    

    def _get_current_user(self):
        request = self.context.get('request', None)
        if request.user == 'AnonymousUser':
            return 'AnonymousUser' #request.user
        else :
            return request.user
        

class 생산계획_BG용_Serializer( serializers.ModelSerializer):

    class Meta:
        model = 생산계획실적        
        fields = '__all__'
        read_only_fields = ['id']

    def create(self, validated_data):
        _instance = 생산계획실적.objects.using('생산모니터링').create(**validated_data)
        _instance.save()

        return _instance