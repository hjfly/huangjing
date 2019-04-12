# -*- coding: utf-8 -*-
"""
urls config
"""
from django.conf.urls import patterns

urlpatterns = patterns(
    'huangjing_330.views',
    (r'^api/test$', 'api_test'),
    (r'^api/set_list', 'set_list'),
    (r'^api/change_set_host', 'change_set_host'),
    (r'^api/execute_job', 'execute_job'),
    (r'^api/job_records', 'job_records'),
    (r'^log_records_list', 'log_records_list'),
    (r'^statistics_list', 'statistics_list'),
    (r'^statistics_data', 'statistics_data'),
    (r'^', 'index'),

)
