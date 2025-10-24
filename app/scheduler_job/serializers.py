"""
Serializers for release App
"""
from django.conf import settings
from rest_framework import serializers

# from users.models import Api_App권한, User
from . import models as Scheduler_Job_Models
from config.models import WS_URLS_DB


class JOB_INFO_Serializer(serializers.ModelSerializer):
    ws_url_db = serializers.PrimaryKeyRelatedField(queryset=WS_URLS_DB.objects.all())
    ws_url_name = serializers.ReadOnlyField()
    redis_channel = serializers.ReadOnlyField()
    
    class Meta:
        model = Scheduler_Job_Models.JOB_INFO
        fields = [f.name for f in model._meta.fields] + ['ws_url_name', 'redis_channel']
        read_only_fields = ['id']




class Scheduler_Job_Serializer(serializers.ModelSerializer):
    job_info = serializers.PrimaryKeyRelatedField(queryset=Scheduler_Job_Models.JOB_INFO.objects.all())
    job_info_data = serializers.SerializerMethodField(read_only=True)
    job_info_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Scheduler_Job_Models.Scheduler_Job
        fields = [f.name for f in model._meta.fields] + ['job_info_name', 'job_info_data']
        read_only_fields = ['id', 'created_time', 'updated_time', 'created_by', 'updated_by']

    def get_job_info_data(self, obj):
        return JOB_INFO_Serializer(obj.job_info).data

    def get_job_info_name(self, obj):
        try:
            return obj.job_info.name
        except:
            return 'job_info_name'

class Scheduler_Job_Status_Serializer(serializers.ModelSerializer):
    job_info = serializers.SerializerMethodField()
    job_info_name = serializers.SerializerMethodField()
    job_schedule = serializers.SerializerMethodField()
    class Meta:
        model = Scheduler_Job_Models.Scheduler_Job_Status
        fields = [f.name for f in model._meta.fields] + ['job_info', 'job_info_name', 'job_schedule']
        read_only_fields = ['id']

    def get_job_info(self, obj):
        return JOB_INFO_Serializer(obj.job.job_info).data
    
    def get_job_info_name(self, obj):
        return obj.job.job_info.name

    def get_job_schedule(self, obj):
        return Scheduler_Job_Serializer(obj.job).data


class Scheduler_Job_Log_Serializer(serializers.ModelSerializer):
    job_info_name = serializers.SerializerMethodField()
    class Meta:
        model = Scheduler_Job_Models.Scheduler_Job_Log
        fields = [f.name for f in model._meta.fields] + ['job_info_name']
        read_only_fields = ['id']

    def get_job_info_name(self, obj):
        return obj.job.job_info.name