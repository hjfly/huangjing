# -*- coding: utf-8 -*-
"""
celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import datetime

from celery import task
from celery.schedules import crontab
from celery.task import periodic_task
from blueking.component.shortcuts import get_client_by_user
from models import JobRecord
from common.log import logger
from django.conf import settings
from django.forms.models import model_to_dict
from common.utils import CJsonEncoder
import json


@task()
def async_task(x, y):
    """
    定义一个 celery 异步任务
    """
    logger.error(u"celery 定时任务执行成功，执行结果：{:0>2}:{:0>2}".format(x, y))
    return x + y


def execute_task():
    """
    执行 celery 异步任务

    调用celery任务方法:
        task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
        task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
        delay(): 简便方法，类似调用普通函数
        apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
                      详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
    """
    now = datetime.datetime.now()
    logger.error(u"celery 定时任务启动，将在60s后执行，当前时间：{}".format(now))
    # 调用定时任务
    async_task.apply_async(args=[now.hour, now.minute], eta=now + datetime.timedelta(seconds=60))


@periodic_task(run_every=crontab(minute='*/5', hour='*', day_of_week="*"))
def get_time():
    """
    celery 周期任务示例

    run_every=crontab(minute='*/5', hour='*', day_of_week="*")：每 5 分钟执行一次任务
    periodic_task：程序运行时自动触发周期任务
    """
    execute_task()
    now = datetime.datetime.now()
    logger.error(u"celery 周期任务调用成功，当前时间：{}".format(now))


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week="*"))
def sync_job_records():
    """
    定时获取快速脚本执行记录

    run_every=crontab(minute='*/1', hour='*', day_of_week="*")：每 1 分钟执行一次任务
    :return:
    """
    execute_task()
    # 查询所有需要执行的任务（脚本执行状态为未完成的任务状态）
    unfinished_scripts = JobRecord.objects.filter(result=0)
    if unfinished_scripts.exists():
        # 所有未完成的任务调用API查询状态
        client = get_client_by_user(settings.ADMINS)
        for script in unfinished_scripts:
            script_dict = model_to_dict(script)
            args = dict()
            args["bk_app_code"] = settings.APP_ID
            args["bk_app_secret"] = settings.APP_TOKEN
            args["bk_username"] = script_dict["user"]
            args["bk_biz_id"] = script_dict["biz_id"]
            args["job_instance_id"] = script_dict["job_id"]
            logger.error('get_job_instance_status, params is {}'.format(args))
            api_result = client.job.get_job_instance_status(args)
            logger.error('get_job_instance_status, result is {}'.format(api_result))
            # print api_result
            if api_result["code"] == 0:
                logger.error("invoke api success")
                if api_result["data"]["is_finished"]:
                    script.result = 1
                    script.log = get_job_log(client, args)
                    script.status = api_result["data"]["job_instance"]["status"]
                else:
                    script.status = 2
                script.save()
            else:
                logger.error("invoke api error")


def get_job_log(client, args):
    api_result = client.job.get_job_instance_log(args)
    print api_result
    logs = []
    for item in api_result["data"][0]["step_results"]:
        log_info = {}
        for ip_log in item["ip_logs"]:
            log_info['ip'] = ip_log["ip"]
            log_info['content'] = ip_log["log_content"]
            logs.append(log_info)
    return json.dumps(logs, cls=CJsonEncoder)


def send_Email(user, content):
    # receiver_address = MailInfo.objects.filter(name=user).values("email_address")
    # if len(receiver_address) < 1:
    #     # 当操作用户不在邮件接收列表中时，则向默认邮件接收人发送邮件
    #     logger.info("当前执行用户不在邮件发送用户中，发送邮件给默认邮件接收用户")
    receiver_address_list = []
    receiver_address=[]
    for address in receiver_address:
        receiver_address_list.append(address['email_address'])
    receiver = ",".join(receiver_address_list)
    client = get_client_by_user(user)
    kwargs = {
        'bk_app_code': settings.APP_ID,
        'bk_app_secret': settings.APP_TOKEN,
        'bk_username': user,
        'receiver': receiver,
        'title': u'有孚云常用查询脚本执行结果通知',
        'content': content,
        'body_format': "Html"
    }
    result = client.cmsi.send_mail(kwargs)
    if result['result']:
        logger.info(u"邮件已发送至%s" % receiver)
        #MailRecords.objects.create(receiver=receiver, content=content, sent_state="success")
    else:
        logger.info(u"邮件发送失败:%s" % result['message'])
        #MailRecords.objects.create(receiver=receiver, content=content, sent_state="failed")




