from typing import Iterable
from django.conf import settings
from django.db import models
from django.apps import apps

from django.utils import timezone

from datetime import datetime, date

import uuid

class Dummy(models.Model):
    id = models.AutoField(primary_key=True)

    class Meta:
        managed = True
        db_table = "dummy_table"

def icons_directory_path(instance, filename):
    return ( f'config/icons/{instance.title}/' + str(uuid.uuid4()) +'/'+ filename) 

def directory_path(instance, filename):
    # now = datetime.now()
    return ( f'config/resources/{instance.name}/' + str(uuid.uuid4()) +'/'+ filename) 

class WS_URLS_DB(models.Model):
    """ 웹소켓 연결 주소 """
    app_fk = models.ForeignKey(to="users.Api_App권한", on_delete=models.DO_NOTHING, null=True, blank=True , related_name='ws_urls_db_app_fk')
    group = models.CharField(max_length=250, default='group필수')
    channel = models.CharField(max_length=250, default='channel필수')
    name = models.CharField(max_length=250, default='unique 한 통상적인 이름', unique=True )
    is_active = models.BooleanField(default=True )
    TO_MODEL = models.CharField(max_length=250, default='')

    is_init = models.BooleanField(default=False )

    def __str__(self):
        """ 웹소켓 연결 주소 표현 """
        return f"{self.group}/{self.channel}"
    
    def get_related_model(self):
        """문자열로부터 실제 모델 클래스를 가져옵니다."""
        if not self.TO_MODEL:
            return None
        try:
            app_label, model_name = self.TO_MODEL.split('.')
            model_class = apps.get_model(app_label, model_name)
            return model_class
        except (ValueError, LookupError):
            return None
    
    def get_related_objects(self):
        """관련 모델의 모든 객체를 가져옵니다."""
        model_class = self.get_related_model()
        if model_class:
            return model_class.objects.all()
        return None

# class Icons ( models.Model ):
#     file = models.FileField(upload_to=directory_path, max_length=255)


# class Header_Menus_Details(models.Model):
#     icon_fk = models.ForeignKey(Icons , on_delete=models.DO_NOTHING, null=True, blank=True )
#     title = models.CharField(default='title', max_length= 250 )
#     tooltip = models.CharField(default='tooltip', max_length= 250 )
#     objectName =models.CharField(default='objectName', max_length= 250 )
#     enabled = models.BooleanField(default=True )


### 최상단 table 
class Table(models.Model):
    table_name = models.CharField( max_length=50, blank=True, null=True)

### 테이블 메뉴들
class V_Header_Menus(models.Model):
    name = models.CharField( max_length=50, blank=True, null=True)
    title = models.CharField( max_length=50, blank=True, null=True)
    tooltip = models.CharField( max_length=50, blank=True, null=True)

class H_Header_Menus(models.Model):
    name = models.CharField( max_length=50, blank=True, null=True)
    title = models.CharField( max_length=50, blank=True, null=True)
    tooltip = models.CharField( max_length=50, blank=True, null=True)
    

class Cell_Menus(models.Model):
    name = models.CharField( max_length=50, blank=True, null=True)
    title = models.CharField( max_length=50, blank=True, null=True)
    tooltip = models.CharField( max_length=50, blank=True, null=True)


# ---  m2m 중간 테이블들 ---
class TableVHeaderLink(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    menu = models.ForeignKey(V_Header_Menus, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)

class TableHHeaderLink(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    menu = models.ForeignKey(H_Header_Menus, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)

class TableCellMenuLink(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    cell_menu = models.ForeignKey(Cell_Menus, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)





    
    

# class DB_Field(models.Model):
#     # file_fks =  models.ManyToManyField( 부적합_file )
    
#     api_app_fk = models.ForeignKey( Api_App권한,  on_delete=models.DO_NOTHING,  null=True, blank=True)

#     fields_append = models.JSONField( default='{}' )
#     fields_delete = models.JSONField(  default='{}' )



def get_default_cell_style():
    return {}

    return {
        "background": '#f0f0f0',
        "foreground": '#000000',
        "font": {
            "family": "Arial",
            "size": 12,
            "bold": True,
            "italic": False
        },
        "alignment": "center"
    }

def get_default_table_style():
    """ stylesheet 형식으로 text 형식으로 저장되어야 함 """
    return  None

class Table_Config(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True, blank=True)
    table_name = models.CharField(max_length= 250, default='table_name' )
    table_style = models.CharField(max_length= 250, default=get_default_table_style , null=True, blank=True )
    column_name = models.CharField(max_length= 250, default='columns_name' )
    display_name = models.CharField(max_length= 250, default='display_name' )
    column_type = models.CharField(max_length= 250, default='CharField' )
    column_width = models.IntegerField(default=0 )
    cell_style = models.JSONField(default=get_default_cell_style )
    is_editable = models.BooleanField(default=True )
    is_hidden = models.BooleanField(default=False )

    header_menu = models.CharField(max_length= 250, null=True, blank=True )
    cell_menu = models.CharField(max_length= 250, null=True, blank=True )

    order = models.IntegerField(default=0 )


class Resources(models.Model):
    name = models.CharField(max_length= 250, default='resources_name' )
    file = models.FileField(upload_to=directory_path, max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


from django.core.validators import RegexValidator

hex_color_validator = RegexValidator(
    regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$',
    message="색상은 #RRGGBB 또는 #RRGGBBAA 형식이어야 합니다."
)

class ColorScheme(models.Model):
    name = models.CharField(max_length=50, unique=True)  # READY, RUNNING ...
    bg = models.CharField(max_length=12, validators=[hex_color_validator])                 # "#E6F0FF"
    font = models.CharField(max_length=12, validators=[hex_color_validator])               # "#003C78"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=10, default="server")