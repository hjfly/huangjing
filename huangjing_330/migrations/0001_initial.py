# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='JobRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length=255)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('biz_id', models.CharField(max_length=255)),
                ('biz_name', models.CharField(max_length=255)),
                ('host_list', models.CharField(max_length=255)),
                ('result', models.IntegerField()),
                ('job_id', models.CharField(max_length=255)),
                ('log', models.TextField(null=True, blank=True)),
                ('status', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'db_table': 'job_record',
            },
        ),
        migrations.CreateModel(
            name='TaskExecScript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('name', models.CharField(max_length=64, null=True, blank=True)),
                ('content', models.TextField(null=True, blank=True)),
                ('args', models.CharField(max_length=255, null=True, blank=True)),
                ('argsformat', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('args_not_empty', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'task_exec_script',
            },
        ),
    ]
