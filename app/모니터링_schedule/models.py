from django.db import models
from django.utils import timezone
from datetime import date, datetime, timedelta


class App (models.Model):
    title = models.CharField(max_length=100, default='', help_text='schedule 명칭 ')
    script = models.CharField(max_length=250, default='', help_text='app 실행 script ')
    설명 = models.TextField(blank=True, null=True)

    server기록 = models.DateTimeField ( default=timezone.now )

class Hour_Schedule(models.Model): 

    title  = models.CharField(max_length=100, default='', help_text='schedule 명칭 ')
    # schedule = models.JSONField(default='{}', help_text= "json filed임 {'key':'value'}")
    schedule = models.TextField(blank=True, null=True, help_text="json stringpy하여 저장함")

    app_fk = models.ForeignKey(App ,null=True, on_delete=models.SET_NULL )
 
    server기록 = models.DateTimeField ( default=timezone.now )