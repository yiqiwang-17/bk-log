# -*- coding=utf-8 -*-
"""
Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
License for BK-LOG 蓝鲸日志平台:
--------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""
MONITOR 模块，调用接口汇总
"""
from django.utils.translation import ugettext_lazy as _  # noqa

from apps.api.modules.utils import add_esb_info_before_request  # noqa
from config.domains import MONITOR_APIGATEWAY_ROOT  # noqa
from apps.api.base import DataAPI  # noqa


class _MonitorApi(object):
    MODULE = _("MONITOR")

    def __init__(self):
        self.save_alarm_strategy = DataAPI(
            method="POST",
            url=MONITOR_APIGATEWAY_ROOT + "save_alarm_strategy/",
            module=self.MODULE,
            description=u"保存告警策略",
            default_return_value=None,
            before_request=add_esb_info_before_request,
        )


MonitorApi = _MonitorApi()
