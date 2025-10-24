"""
Serializers for release App
"""
from django.conf import settings
from rest_framework import serializers

# from users.models import Api_App권한, User
from release.models import (
    Release관리
)

from util.utils_func import CustomDecimalField

def model_to_dict_custom(instance):
    model_dict = {}
    # Iterate through the model instance's fields
    for field in instance._meta.fields:
        field_name = field.name
        if ( 'NCR_fk' in field_name) :   field_value = instance.NCR_fk_id
        else :   field_value = getattr(instance, field_name)
        # Convert special types if needed (e.g., datetime to string)
        if hasattr(field_value, 'strftime'):
            field_value = field_value.strftime('%Y-%m-%d %H:%M:%S')
        model_dict[field_name] = field_value
    return model_dict

def _getClientIP(obj):
    x_forwarded_for = obj.context.get('request').META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = obj.context.get('request').META.get('REMOTE_ADDR')
    return ip    

class Release관리_Serializer(serializers.ModelSerializer):
    # https://stackoverflow.com/questions/28945327/django-rest-framework-with-choicefield
    # OS_CHOICES = serializers.CharField(source='get_OS_display')
    버젼 = CustomDecimalField(max_digits=5, decimal_places=2,  coerce_to_string=False)
    OS_choices = serializers.SerializerMethodField()
    종류_choices = serializers.SerializerMethodField()

    class Meta:
        model = Release관리
        fields =[f.name for f in Release관리._meta.fields]  + ['OS_choices','종류_choices']
        read_only_fields = ['id'] 

    def get_OS_choices(self, obj=None):
        return [{'value': val, 'display': label} for val, label in Release관리.OS_CHOICES]

    def get_종류_choices(self, obj=None):
        return [{'value': val, 'display': label} for val, label in Release관리.종류_CHOICES]
