"""
Serializers for Config
"""
from django.conf import settings
from rest_framework import serializers
from django.core import serializers as core_serializer
# https://medium.com/django-rest/django-rest-framework-login-and-register-user-fd91cf6029d5

from datetime import datetime, date,time, timedelta
import datetime as dt
import time
from django.utils import timezone
from . import models as Config_Models
from users.models import Api_App권한


class WS_URLS_DB_Serializer(serializers.ModelSerializer):
    app_fk = serializers.PrimaryKeyRelatedField(queryset=Api_App권한.objects.all(), 
                                                required=False,  # 이거 반드시 추가!
                                                allow_null=True  # null 입력도 허용)
    )
    class Meta:
        model = Config_Models.WS_URLS_DB
        fields =[f.name for f in model._meta.fields] 



class Table_Config_Serializer(serializers.ModelSerializer):
    table_name = serializers.SerializerMethodField()
    class Meta:
        model = Config_Models.Table_Config
        fields = '__all__'

    def get_table_name(self, instance):
        return instance.table.table_name


class Resources_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.Resources
        fields = '__all__'

class Table_Serializer(serializers.ModelSerializer):
    config = Table_Config_Serializer(many=True)
    menus = serializers.SerializerMethodField()

    class Meta:
        model = Config_Models.Table
        fields = ['id', 'table_name'] + ['config', 'menus']

    def get_menus(self, obj):
        v_header_links = Config_Models.TableVHeaderLink.objects.filter(table=obj).order_by('order')
        h_header_links = Config_Models.TableHHeaderLink.objects.filter(table=obj).order_by('order')
        cell_menu_links = Config_Models.TableCellMenuLink.objects.filter(table=obj).order_by('order')
        
        v_header_menus = TableVHeaderLink_Serializer(v_header_links, many=True).data
        h_header_menus = TableHHeaderLink_Serializer(h_header_links, many=True).data
        cell_menus = TableCellMenuLink_Serializer(cell_menu_links, many=True).data

        return {
            'v_header': v_header_menus,
            'h_header': h_header_menus,
            'cell_menus': cell_menus
        }

class Table_Only_Name_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.Table
        fields = ['id', 'table_name']

class V_Header_Menus_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.V_Header_Menus
        fields = '__all__'


class H_Header_Menus_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.H_Header_Menus
        fields = '__all__'


class Cell_Menus_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.Cell_Menus
        fields = '__all__'


class  TableVHeaderLink_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.TableVHeaderLink
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['v_header'] = V_Header_Menus_Serializer(instance.menu).data
        return data

class TableHHeaderLink_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.TableHHeaderLink
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['h_header'] = H_Header_Menus_Serializer(instance.menu).data
        return data

class TableCellMenuLink_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.TableCellMenuLink
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cell_menu'] = Cell_Menus_Serializer(instance.cell_menu).data
        return data
    

class ColorScheme_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Config_Models.ColorScheme
        fields = [ f.name for f in model._meta.fields]
