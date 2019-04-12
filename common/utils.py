# -*- coding: utf-8 -*-
"""
开发框架公用方法
1. 页面输入内容转义（防止xss攻击）
from common.utils import html_escape, url_escape, texteditor_escape
2. 转义html内容
html_content = html_escape(input_content)
3. 转义url内容
url_content = url_escape(input_content)
4. 转义富文本内容
texteditor_content = texteditor_escape(input_content)
"""
from common.pxfilter import XssHtml
from blueking.component.shortcuts import get_client_by_request, get_client_by_user
from common.log import logger
from conf.default import APP_ID, APP_TOKEN
import uuid
import base64
from decimal import Decimal
from datetime import date, datetime
from math import ceil


import json
def unicode_2_utf8(para):
    if type(para) is str:
        return para.encode('utf-8')
    elif type(para) is list:
        for i in range(len(para)):
            para[i] = unicode_2_utf8(para[i])
        return para
    elif type(para) is dict:
        newpara = {}
        for (key, value) in para.items():
            key = unicode_2_utf8(key)
            value = unicode_2_utf8(value)
            newpara[key] = value
        return newpara
    elif type(para) is tuple:
        return tuple(unicode_2_utf8(list(para)))
    elif type(para) is unicode:
        return para.encode('utf-8')
    else:
        return para


def html_escape(html, is_json=False):
    """
    Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true, the quotation mark character (")
    is also translated.
    rewrite the cgi method
    @param html: html代码
    @param is_json: 是否为json串（True/False） ，默认为False
    """
    # &转换
    if not is_json:
        html = html.replace("&", "&amp;")  # Must be done first!
    # <>转换
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")
    # 单双引号转换
    if not is_json:
        html = html.replace(' ', "&nbsp;")
        html = html.replace('"', "&quot;")
        html = html.replace("'", "&#39;")
    return html


def url_escape(url):
    url = url.replace("<", "")
    url = url.replace(">", "")
    url = url.replace(' ', "")
    url = url.replace('"', "")
    url = url.replace("'", "")
    return url


def texteditor_escape(str_escape):
    """
    富文本处理
    @param str_escape: 要检测的字符串
    """
    try:
        parser = XssHtml()
        parser.feed(str_escape)
        parser.close()
        return parser.get_html()
    except Exception, e:
        logger.error(u"js脚本注入检测发生异常，错误信息：%s" % e)
        return str_escape


class UUIDTools(object):
    """uuid function tools"""

    @staticmethod
    def uuid1_hex():
        """
        return uuid1 hex string

        eg: 23f87b528d0f11e696a7f45c89a84eed
        """
        return uuid.uuid1().hex


def client_and_common_args(request=None, user=None):
    if request:
        client = get_client_by_request(request)
    else:
        client = get_client_by_user(user)

    kwargs = {
        "bk_app_code": APP_ID,
        "bk_app_secret": APP_TOKEN,
    }
    if request:
        bk_token = request.COOKIES.get('bk_token', '')
        kwargs['bk_token'] = bk_token
    else:
        kwargs['bk_username'] = user

    return client, kwargs


def search_business(request=None, user=None):
    """查询业务"""
    client, kwargs = client_and_common_args(request, user)
    result = client.cc.search_business(kwargs)
    logger.debug('search business, result is {}'.format(result))
    if result['result'] is False:
        logger.warning('search business false, msg is {}'.format(result))
    return result['result'], result['data'], result['message']


def search_host(bk_biz_id=None, request=None, user=None):
    """查询主机"""
    client, kwargs = client_and_common_args(request, user)
    if bk_biz_id:
        kwargs['bk_biz_id'] = bk_biz_id
    result = client.cc.search_host(kwargs)
    logger.debug('search host, result is {}'.format(result))
    if result['result'] is False:
        logger.warning('search host false, msg is {}'.format(result))
    return result['result'], result['data'], result['message']


def fast_execute_script(bk_biz_id, script_type=None, script_content=None,
                        account="root", ip_list=[], request=None, user=None):
    """快速执行脚本

    :param bk_biz_id: 业务ID
    :param script_type: 脚本类型：1(shell脚本)、2(bat脚本)、3(perl脚本)、4(python脚本)、5(Powershell脚本)
    :param script_content: 脚本内容Base64，如果同时传了script_id和script_content，则script_id优先
    :param request:
    :param user:
    :return:
    """
    """"""
    client, kwargs = client_and_common_args(request, user)
    kwargs['script_type'] = script_type
    kwargs['bk_biz_id'] = bk_biz_id
    kwargs['ip_list'] = ip_list
    kwargs['account'] = account
    kwargs['script_timeout'] = 3
    if script_content:
        kwargs['script_content'] = base64.encodestring(script_content)
    result = client.job.fast_execute_script(kwargs)
    logger.debug('fast execute script, result is {}'.format(result))
    if result['result'] is False:
        logger.warning('fast execute script, msg is {}'.format(result))
    # 补充获取结果的方法
    return result['result'], result['data'], result['message']


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return '%.2f' % obj
        else:
            return json.JSONEncoder.default(self, obj)



def get_base_pager_by_request(request):
    if 'asc' == request.POST.get('orderType'):
        orderStr = request.POST.get('orderName')
    else:
        orderStr = '-' + request.POST.get('orderName')
    start = request.POST.get('start')
    length = request.POST.get('length')
    page_num = ceil((float(start) + 1) / (int(length)))
    return {
        'draw': request.POST.get('draw'),
        'orderStr': str(orderStr),
        'page_num': page_num,
        'length': int(request.POST.get('length'))
    }



def str_to_boolean(s):
    if not s:
        return False
    if s.lower() == 'true' or s.lower == '1':
        return True
    return False


# 1.把datetime转成字符串
def datetime_toString(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# 2.把字符串转成datetime
def string_toDatetime(st):
    return datetime.strptime(st, "%Y-%m-%d %H:%M:%S")


# 3.把字符串转成时间戳形式
def string_toTimestamp(st):
    return datetime.mktime(datetime.strptime(st, "%Y-%m-%d %H:%M:%S"))


# 4.把时间戳转成字符串形式
def timestamp_toString(sp):
  return datetime.strftime("%Y-%m-%d %H:%M:%S", datetime.localtime(sp))


# 5.把datetime类型转外时间戳形式
def datetime_toTimestamp(dt):
    return datetime.mktime(dt.timetuple())