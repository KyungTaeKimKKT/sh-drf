"""
Serializers for 일일보고
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5
from rest_framework.fields import CurrentUserDefault

from datetime import datetime, date,time, timedelta
import datetime as dt
import time



from 일일보고.models import (
    ISSUE_리스트_DB,
    개인_리스트_DB, 
    휴일_DB,  
    조직_INFO,
    개인_INFO,
    전기사용량_DB,
)

class 개인_INFO_Serializer(serializers.ModelSerializer):
    class Meta:
        model = 개인_INFO
        fields ='__all__'

    

class 개인_리스트_DB_Serializer(serializers.ModelSerializer):
    보고자 = serializers.SerializerMethodField()
    조직 = serializers.SerializerMethodField()

    class Meta:
        model = 개인_리스트_DB
        # https://stackoverflow.com/questions/64476816/how-to-add-new-serializer-field-along-with-the-all-model-fields
        # fields = [f.name for f in 개인_리스트_DB._meta.fields] + ['일자list' ] - ['등록자_id',['조직이름_id']]
        fields = '__all__'
        # fields = ['id','일자','업무내용','업무주기','소요시간','주요산출물','비고' ] #,'일자list']
        read_only_fields = ['id']

    #### SerializerMethodField 사용
    def get_보고자(self, obj):
        return obj.등록자_id.user_fk.user_성명

    def get_조직(self, obj):
        return obj.조직이름_id.조직이름

    def _get_일자list(self, instance):
        day_list =[]
        day = datetime.today()
        delta = timedelta(days=1)
        while ( len(day_list) <= 2 ):
            if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
            day -=delta
        return sorted(day_list)
    
    def _get_current_user(self):
        request = self.context.get('request', None)
        if request.user == 'AnonymousUser':
            return 'AnonymousUser' #request.user
        else :
            return request.user

    def _get_등록자_id(self, id, instance):
        for key, value in id.items():
            print ( key , ":  ", value )
            instance.등록자_id = 개인_INFO.objects.get(user_fk=value)

        # instance.등록자_id.add(개인_INFO.objects.get(user_fk=user_fk))


    def create(self, validated_data):
        validated_data['등록자_id'] = 개인_INFO.objects.get(user_fk= self._get_current_user()) 
        validated_data['조직이름_id'] = 조직_INFO.objects.get( 조직이름 = self._get_current_user().기본조직1) 

        instance = 개인_리스트_DB.objects.create (**validated_data)
        return instance
    


class 조직_리스트_DB_Serializer(serializers.ModelSerializer):
    보고자 = serializers.SerializerMethodField()
    조직 = serializers.SerializerMethodField()
    # 등록자_id = 개인_INFO_Serializer(read_only=True )
    # 일자list = serializers.SerializerMethodField('_get_일자list')
    # is전기등록 = serializers.SerializerMethodField('_get_is전기등록')

    class Meta:
        model = ISSUE_리스트_DB
        fields = [f.name for f in ISSUE_리스트_DB._meta.fields] + ['보고자', '조직']
        # fields = ['id','일자','활동현황','세부내용','완료예정일','진척율','유관부서','비고',]#'일자list'] +['is전기등록']
        read_only_fields = ['id']

    #### SerializerMethodField 사용
    def get_보고자(self, obj):
        return obj.등록자_id.user_fk.user_성명

    def get_조직(self, obj):
        return obj.조직이름_id.조직이름

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['보고자'] = instance.등록자_id.user_fk.user_성명
    #     data['조직'] = instance.조직이름_id.조직이름
    #     return data

    def _get_일자list(self, instance):
        day_list =[]
        day = datetime.today()
        delta = timedelta(days=1)
        while ( len(day_list) <= 2 ):
            if ( not 휴일_DB.objects.filter( 휴일= day) ): day_list.append(day)
            day -=delta
        return sorted(day_list)
    
    def _get_is전기등록(self, instance):
        qs = 개인_INFO.objects.filter(user_fk = self._get_current_user(), is_전기사용=True)
        return qs.count() >0 

    def _get_current_user(self):
        request = self.context.get('request', None)
        if request.user == 'AnonymousUser':
            return 'AnonymousUser' #request.user
        else :
            return request.user

    def create(self, validated_data):
        validated_data['등록자_id'] = 개인_INFO.objects.get(user_fk= self._get_current_user()) 
        validated_data['조직이름_id'] = 조직_INFO.objects.get( 조직이름 = self._get_current_user().기본조직1) 

        instance = ISSUE_리스트_DB.objects.create (**validated_data)
        return instance


class 전기사용량_DB_Serializer(serializers.ModelSerializer):
    today = serializers.SerializerMethodField('_get_today', read_only=True)
    class Meta:
        model = 전기사용량_DB
        fields = ['id','등록자','하이전기_file','폴리전기_file','일자'] +['today']
        read_only_fields = ['id','today']

    def _get_today(self, instance) -> str:
        """ 보고용 오늘 날자 return """
        from 일일보고.views import get_3days
        today = get_3days()[1]
        return today.strftime('%Y-%m-%d')
    



class 휴일등록_DB__Serializer(serializers.ModelSerializer):
    class Meta:
        model = 휴일_DB
        fields ='__all__'
        read_only_fields = ['id']