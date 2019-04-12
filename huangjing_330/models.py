

# Create your models here.

from django.db import models
from datetime import datetime

# Create your models here.


class JobRecord(models.Model):
    user = models.CharField(max_length=255)
    created = models.DateTimeField(default=datetime.now)
    biz_id = models.CharField(max_length=255)
    biz_name = models.CharField(max_length=255)
    host_list = models.CharField(max_length=255)
    result = models.IntegerField()
    job_id = models.CharField(max_length=255)
    log = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'job_record'


class TaskExecScript(models.Model):
    created = models.DateTimeField(default=datetime.now)
    name = models.CharField(max_length=64, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    args = models.CharField(max_length=255, blank=True, null=True)
    argsformat = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    args_not_empty = models.BooleanField(default=False)

    class Meta:
        db_table = 'task_exec_script'

