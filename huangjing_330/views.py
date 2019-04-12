# -*- coding: utf-8 -*-
import conf.default
from conf.default import APP_TOKEN,APP_ID

# Create your views here.
from django.core.paginator import Paginator
from common.mymako import render_mako_context
from common.mymako import render_json
from blueking.component.shortcuts import get_client_by_request
from account.decorators import login_exempt
from models import JobRecord
from common.utils import CJsonEncoder
from common import utils
import json
import datetime
import logging
from django.db.models import Q, Count
from models import TaskExecScript
import base64

logger = logging.getLogger(APP_ID)

@login_exempt
def api_test(request):
    if request.user:
        data = {"user": request.user.username, "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    else:
        data = {"time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    return render_json({"result": "true", "message": "hellworld", "data": data})


def index(request):
    client = get_client_by_request(request)
    kwargs = {'bk_app_secret': APP_TOKEN, 'bk_app_code': conf.default.APP_ID}
    result_biz = client.cc.search_business(kwargs)
    bk_biz_id = result_biz['data']['info'][0]['bk_biz_id']
    set_params = query_set_params(bk_biz_id)
    result_set = client.cc.search_set(set_params)
    logger.debug(result_set)
    if result_set and result_set['data']['info'] and result_set['data']['info'][0]['bk_set_id']:
        bk_set_id = result_set['data']['info'][0]['bk_set_id']
        host_args = query_host_params(bk_set_id, bk_biz_id)
        result_host = client.cc.search_host(host_args)
        return render_mako_context(request, '/huangjing/index.html',
                                   {'business_list': result_biz['data']['info'], "set_list": result_set['data']['info'],
                                    "host_list": result_host['data']['info']})
    else:
        return render_mako_context(request, '/huangjing/index.html',
                                   {'business_list': result_biz['data']['info'], "set_list": None,
                                    "host_list": None})


def set_list(request):
    client = get_client_by_request(request)
    bk_biz_id = request.POST.get('bk_biz_id')
    kwargs = query_set_params(bk_biz_id)
    result_set = client.cc.search_set(kwargs)
    if result_set and result_set['data']['info'] and result_set['data']['info'][0]['bk_set_id']:
        bk_set_id = result_set['data']['info'][0]['bk_set_id']
        host_args = query_host_params(bk_set_id, bk_biz_id)
        result_host = client.cc.search_host(host_args)
        return render_json({"set_list": result_set['data']['info'], "host_list": result_host['data']['info']})
    else:
        return render_json({"set_list": result_set['data']['info'], "host_list": None})


def change_set_host(request):
    client = get_client_by_request(request)
    bk_biz_id = request.POST.get('bk_biz_id')
    bk_set_id = request.POST.get('bk_set_id')

    kwargs = query_host_params(bk_set_id, bk_biz_id)
    result_host = client.cc.search_host(kwargs)
    return render_json({"host_list": result_host['data']['info']})


def query_host_params(bk_set_id, bk_biz_id):
    kwargs = {
        "bk_app_code": conf.default.APP_ID,
        "bk_app_secret": APP_TOKEN,
        "ip": {
            "data": [],
            "exact": 1,
            "flag": "bk_host_innerip|bk_host_outerip"
        },
        "condition": [
            {
                "bk_obj_id": "host",
                "fields": [
                ],
                "condition": []
            },
            {"bk_obj_id": "module", "fields": [], "condition": []},
            {"bk_obj_id": "set", "fields": [], "condition": [
                {
                    "field": "bk_set_id",
                    "operator": "$eq",
                    "value": int(bk_set_id)
                }
            ]},
            dict(bk_obj_id="biz", fields=[
                "default",
                "bk_biz_id",
                "bk_biz_name",
            ], condition=[
                {
                    "field": "bk_biz_id",
                    "operator": "$eq",
                    "value": int(bk_biz_id)
                }
            ])
        ],
        #"page": {"start": 0,"limit": 100,"sort": "bk_host_id"},
        "pattern": ""
    }

    return kwargs


def query_set_params(bk_biz_id):
    search_set_params = {'bk_app_code': conf.default.APP_ID, 'bk_app_secret': APP_TOKEN, 'bk_biz_id': bk_biz_id,
                         "fields": ["bk_set_id", "bk_set_name"],
                         "page": {"start": 0, "limit": 100, "sort": "bk_set_name"}}
    # search_set_params["condition"] = {"bk_set_name": "平台"}
    return search_set_params


def execute_job(request):
    client = get_client_by_request(request)
    data = request.POST.get('data')
    data = utils.unicode_2_utf8(json.loads(data))
    bk_biz_id = data['bk_biz_id']
    bk_biz_name = data['bk_biz_name']
    bk_job_id = 4
    kwargs = {'bk_app_secret': APP_TOKEN, 'bk_app_code': conf.default.APP_ID, 'bk_biz_id': bk_biz_id,
              'bk_job_id': bk_job_id}
    result = {"message": "success", "result": "true"}
    job_detail_result = do_get_job_detail(request, kwargs)

    if job_detail_result["code"] == 0:
        job_detail = job_detail_result["data"]
        kwargs["steps"] = []
        if data["ip_list"]:
            for step in job_detail['steps']:
                kwargs["steps"].append({'ip_list': data["ip_list"], 'script_id': step['script_id'],
                                        'step_id': step['step_id']})

        api_result = client.job.execute_job(kwargs)
        # generate record
        record = {"biz_id": bk_biz_id,
                  "biz_name": bk_biz_name,
                  "user": request.user.username,
                  "host_list": json.dumps(data["ip_list"], cls=CJsonEncoder),
                  "job_id": api_result["data"]["job_instance_id"],
                  "result": 0,
                  "status": 2
                  }
        if api_result["code"] == 0:
            # print record
            JobRecord.objects.create(**record)
        else:
            result["message"] = api_result["message"]
            result["result"] = api_result["result"]
    else:
        result["message"] = job_detail_result["message"]
        result["result"] = job_detail_result["result"]
    return render_json(result)


def do_get_job_detail(request, params):
    logger.debug('do_get_job_detail, params is {}'.format(params))
    client = get_client_by_request(request)
    result = client.job.get_job_detail(params)
    logger.debug('do_get_job_detail, result is {}'.format(result))
    return result


def job_records(request):
    """
    分页查询执行记录
    :param request:
    :return:
    """
    base_pager_info = utils.get_base_pager_by_request(request)
    q_query = Q()
    if request.POST.get('bk_biz_id'):
        q_query = q_query & Q(biz_id=request.POST.get('bk_biz_id'))
    if request.POST.get('start_time'):
        q_query = q_query & Q(created__gte=request.POST.get('start_time'))
    if request.POST.get('end_time'):
        q_query = q_query & Q(created__lte=request.POST.get('end_time'))
    page = Paginator(
        JobRecord.objects.filter(q_query).order_by(base_pager_info['orderStr']).values("biz_name", "user", "job_id",
                                                                                       "host_list",
                                                                                       "created", "log", "status"),
        per_page=base_pager_info['length']).page(base_pager_info['page_num'])
    page_list = json.dumps(list(page.object_list), cls=utils.CJsonEncoder)
    return render_json({
        "draw": base_pager_info['draw'],
        "recordsTotal": page.paginator.count,
        "data": json.loads(page_list),
        "recordsFiltered": page.paginator.count
    })


def log_records_list(request):
    client = get_client_by_request(request)
    kwargs = {'bk_app_secret': APP_TOKEN, 'bk_app_code': conf.default.APP_ID}
    result_biz = client.cc.search_business(kwargs)
    return render_mako_context(request, '/huangjing/log_records_list.html',
                               {'business_list': result_biz['data']['info']})


def statistics_list(request):
    client = get_client_by_request(request)
    kwargs = {'bk_app_secret': APP_TOKEN, 'bk_app_code': conf.default.APP_ID}
    result_biz = client.cc.search_business(kwargs)
    return render_mako_context(request, '/huangjing/statistics.html',
                               {'business_list': result_biz['data']['info']})


def statistics_data(request):
    job_status = ['未执行', '正在执行', '执行成功', '执行失败', '跳过', '忽略错误', '等待用户', '手动结束', '状态异常', '步骤强制终止中', '步骤强制终止成功',
                  '步骤强制终止失败']
    q_query = Q()
    if request.POST.get('bk_biz_id'):
        bk_biz_id = request.POST.get('bk_biz_id')
        q_query = q_query & Q(biz_id=bk_biz_id)
    record_data = JobRecord.objects.filter(q_query).values('status').annotate(status_count=Count('status')).order_by(
        "status_count")
    data = []
    if record_data:
        for record in record_data:
            obj = {"name": job_status[int(record["status"]) - 1], "value": record["status_count"]}
            data.append(obj)

    result_data = statistics_params(data)
    return render_json(result_data)


def statistics_params(data):
    return {
        "code": 0,
        "result": True,
        "message": "success",
        "data": {
            "title": "",
            "series": data
        }
    }


def script_execute(request):
    args = request.GET if request.method == "GET" else request.POST
    data = args['data']
    data = utils.unicode_2_utf8(json.loads(data))
    params = {
        'scriptId': data['scriptId'],
        'args': data['args'],
        'vmIds': data['vmIds']
    }
    vm_list = params['vmIds']
    try:
        params['args'].encode('utf-8')
    except:
        return render_json({"result": False, "message": u"请输入正确的参数"})
    if not params['args']:
        return render_json({'result': False, 'message': u'参数中含有敏感命令'})
    if not params['scriptId']:
        return render_json({"result": False, "message": u'请选择脚本'})
    if len(params['vmIds']) < 1:
        return render_json({'result': False, "message": u"请选择至少一台执行主机"})
    if args_must_not_empty_validate(params['scriptId'], params['args']):
        return render_json({'result': False, "message": u'执行当前脚本必须填入参数'})
    else:
        vm = vm_list[0]
        biz = vm['biz']
        ip_list = []
        ip_obj = {
            'bk_cloud_id': vm['bk_cloud_id'],
            'ip': vm['ip']
        }
        ip_list.append(ip_obj)
        task_exec_script = TaskExecScript.objects.get(
            id=params['scriptId'])
        client = get_client_by_request(request)
        _script_content = task_exec_script.content.encode('utf-8')

        script_content = base64.encodestring(_script_content)
        script_param = base64.encodestring(params['args'].encode('utf-8'))

        kwargs = {
            "bk_app_code": conf.default.APP_ID,
            "bk_app_secret": APP_TOKEN,
            "bk_biz_id": biz,
            "bk_username": request.user.username,
            "account": 'root',
            "script_content": script_content,
            'script_param': script_param,
            'script_type': 1,
            'ip_list': ip_list
        }
        logger.info("调用 fast_execute_script 脚本，参数为：{}".format(kwargs))
        result = client.job.fast_execute_script(kwargs)
        vm_address_list = []
        for ip_and_cloud in ip_list:
            ip_address = ip_and_cloud['ip']
            vm_address_list.append(ip_address)
        vm_address = ",".join(vm_address_list)
        if result['result']:
            record = {
                'task_exec_script': task_exec_script,
                'request_json': json.dumps(kwargs),
                'response_json': json.dumps(result),
                'script_args': params['args'],
                'bk_biz_id': kwargs['bk_biz_id'],
                'user': request.user,
                'machine_numbers': len(ip_list),
                'status': 0,
                'vm_ipaddress': vm_address,
                'job_instance_id': result['data']['job_instance_id']
            }
           #TaskExecScriptRecords.objects.create(**record)

        else:
            record = {'task_exec_script': task_exec_script,
                      'request_json': json.dumps(kwargs),
                      'response_json': json.dumps(result),
                      'script_args': params['args'],
                      'bk_biz_id': kwargs['bk_biz_id'],
                      'user': request.user,
                      'machine_numbers': len(ip_list),
                      'vm_ipaddress': vm_address,
                      'status': -1

                      }
           # TaskExecScriptRecords.objects.create(**record)
            logger.error(u'调用接口fast_execute_script失败:{}'.format(result['message']))
        return render_json({"message":u"脚本执行中，请在执行记录中查看执行结果","success":"true"})


def args_must_not_empty_validate(script_id, args):
    script_query = TaskExecScript.objects.get(id=script_id)
    if script_query and args:
        return True
    else:
        return False
