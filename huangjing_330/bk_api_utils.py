# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from blueking.component.shortcuts import get_client_by_request
from blueking.component.shortcuts import get_client_by_user

logger = logging.getLogger("demo")


class BkApiUtil(object):

    @staticmethod
    def search_business(**args):
        """
        查询业务
        """
        if 'fields' not in args:
            # 默认查询业务ID，和业务名称
            args['fields'] = ["bk_biz_id", "bk_biz_name"]
        # logger.debug("call api search_business, args is {%s}" % args)
        bk_business = BkApiUtil.client.cc.search_business(args)
        # logger.debug("call api search_business success, result is {%s}" % bk_business)
        return bk_business["data"]["info"]

    @staticmethod
    def search_set(**args):
        """
        查询集群
        """
        if 'fields' not in args:
            # 默认查询业务ID，和业务名称
            args['fields'] = ["bk_set_id", "bk_set_name"]
        logger.debug("call api search_set, args is {%s}" % args)
        bk_set = BkApiUtil.client.cc.search_set(args)
        logger.debug("call api search_set success, result is {%s}" % bk_set)
        return bk_set["data"]["info"]

    @staticmethod
    def search_host(**args):
        """
        主机查询
        """
        if "condition" not in args:
            # 主机条件
            conditions = [{
                "bk_obj_id": "host",
                "fields": ["bk_host_id", "bk_os_name", "bk_host_innerip", "bk_host_name", "bk_cpu", "bk_os_bit",
                           "bk_os_version"],
                "condition": []
            }, {
                    "bk_obj_id": "biz",
                    "fields": ["bk_biz_id", "bk_biz_name"],
                    "condition": []
            }
            ]
            args.update({"condition": conditions})
        # if "page" not in args:
        #     # 默认最多取100条
        #     page = {
        #         "start": 0,
        #         "limit": 100,
        #         "sort": "bk_host_id"
        #     }
        #     args.update({"page": page})

        bk_hosts = BkApiUtil.client.cc.search_host(args)
        # logger.debug("call api search_set search_host, result is {%s}" % bk_hosts)
        return bk_hosts

    @classmethod
    def setup_bk_client(cls, request=None, user=None, **kwargs):
        """
        获取蓝鲸的client对象
        request和user对象二选一，同时传入，使用request参数
        """
        if request:
            _client = get_client_by_request(request, **kwargs)
        elif user:
            _client = get_client_by_user(user, **kwargs)
        else:
            _client = get_client_by_user(settings.ADMIN_USERNAME, **kwargs)
        cls.client = _client

