from django.conf import settings
from django.db import models


from django.utils import timezone
from users.models import User # custom User model import
from datetime import datetime, date

import uuid
import 생산지시.models as 생지

# class 하이생산계획(models.Model):
#     생산지시_fk =  models.ForeignKey( 생지.생산지시 , on_delete=models.CASCADE, null=True, blank=True )
#     생산지시_process_fk = models.ForeignKey(생지.Process, on_delete=models.CASCADE, null=True, blank=True )
#     공정 = models.CharField(max_length=20,  null=True, blank=True)

#     계획수량 = models.IntegerField(null=True, blank=True)
    
#     계획수립시간 = models.DateTimeField(null=True)
