from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta


class 정부기관_DB(models.Model): 
    gov_id = models.CharField(max_length=20, default='', help_text='moel_news, moel_notice 등으로')
    gov_name = models.CharField(max_length=20, default='', help_text='국토교통부, 고용노동부, 등으로')
    구분 = models.CharField(max_length=15, default='', help_text='공지사항, 보도자료 , 등으로 ')
    url = models.CharField(max_length=150, default='', help_text='URL PAGE FULL로 입력할 것')
    suffix_link = models.CharField(max_length=150, null=True, blank=True,  help_text='URL PAGE FULL로 입력할 것')
 
    server기록 = models.DateTimeField ( default=timezone.now )

    
class NEWS_DB (models.Model): 
    정부기관 = models.CharField(max_length=20, default='', help_text='국토교통부, 고용노동부, 등으로')
    구분 = models.CharField(max_length=15, default='', help_text='공지사항, 보도자료 , 등으로 ')
    제목 = models.CharField(max_length=250, default='', help_text='제목')
    등록일 = models.DateField(max_length=15, default='', help_text='등록일-datefield형태임')
    링크 = models.TextField( default='', help_text='URL PAGE FULL로 입력할 것')
    
    server기록 = models.DateTimeField ( default=timezone.now )
    
class NEWS_Table_Head_DB (models.Model): 
    제목 = models.CharField(max_length=50, blank=True, null=True, default='제목', help_text='제목,..등으로 공란은 없이 ,로 구분')
    등록일 = models.CharField(max_length=50, blank=True, null=True, default='등록일', help_text='등록일,작성일,등으로 공란은 없이 ,로 구분')
    제목금지어 = models.CharField(max_length=254, blank=True, null=True, default='', help_text='공란은 없이 ,로 구분')
    
    server기록 = models.DateTimeField ( default=timezone.now )
    
class NEWS_LOG_DB(models.Model):
    log = models.CharField(max_length=254, blank=True, null=True, default='')
    server기록 = models.DateTimeField ( default=timezone.now )