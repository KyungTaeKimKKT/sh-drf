from django.conf import settings
from django.db import models

from django.utils import timezone
# from users.models import User # custom User model import
# from datetime import datetime, date

import uuid


def release_directory_path(instance, filename):
    # now = datetime.now()
    return ( f'release/{instance.App이름}/{instance.OS}/{instance.버젼}/' + str(uuid.uuid4()) +'/'+ filename) 



class Release관리(models.Model):
    OS_CHOICES = (
        ('W', 'Windows'),
        ('L', 'Linux'),
        ('R', 'RPi')
    )
    종류_CHOICES = (
        ('I', '설치용'),
        ('U', 'Update용'),
    )


    App이름 = models.CharField(max_length=30,  null=True, blank=True)
    OS = models.CharField(max_length=1,  choices=OS_CHOICES, default='W')
    버젼 = models.DecimalField(max_digits=5, decimal_places=2,  default=0.01)
    종류 = models.CharField(max_length=1,  choices=종류_CHOICES, default='U' )
    file = models.FileField(upload_to=release_directory_path, max_length=254, null=True, blank=True)

    is_즉시 = models.BooleanField ( default=True )
    is_release = models.BooleanField ( default=True)

    timestamp = models.DateTimeField(default=timezone.now() )

    변경사항 = models.TextField(default='')

    def save(self, *args, **kwargs):
        self.버젼 = round(self.버젼, 2)
        super().save(*args, **kwargs)

