# -*- coding: utf-8 -*-
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
import random

from django.utils.translation import ugettext_lazy as _

from apps.log_extract.components.collections.base_component import BaseService
from apps.log_extract import constants
from apps.log_extract.fileserver import FileServer
from apps.log_extract.models import Tasks, ExtractLink, ExtractLinkHost
from apps.log_extract.utils.packing import get_packed_dir_name
from pipeline.component_framework.component import Component
from pipeline.core.flow.activity import Service, StaticIntervalGenerator


class FileDistributionService(BaseService):
    name = _("文件分发")
    __need_schedule__ = True
    interval = StaticIntervalGenerator(BaseService.TASK_POLLING_INTERVAL)

    def __init__(self):
        super().__init__(name=self.name)

    def inputs_format(self):
        return [
            Service.InputItem(name=_("任务ID"), key="task_id", type="str", required=True),
            Service.InputItem(name=_("源文件信息列表"), key="file_source_list", type="list", required=True),
            Service.InputItem(name=_("用户名"), key="username", type="str", required=False),
            Service.InputItem(name=_(_("执行脚本机器的用户名")), key="account", type="str", required=False),
            Service.InputItem(name=_("业务id"), key="bk_biz_id", type="str", required=True),
            Service.InputItem(name=_("作业执行人"), key="operator", type="str", required=True),
        ]

    def outputs(self):
        return [
            Service.OutputItem(name=_("分发任务instance id"), key="task_instance_id", type="int"),
            Service.OutputItem(name=_("分发服务器IP地址"), key="distribution_ip", type="str"),
            Service.OutputItem(name=_("分发服务器中转文件路径"), key="transit_server_file_path", type="list"),
            Service.OutputItem(name=_("分发后打包步骤的打包路径"), key="transit_server_packing_file_path", type="str"),
        ]

    def _poll_status(self, task_instance_id, operator, bk_biz_id):
        return FileServer.query_task_result(task_instance_id, operator, bk_biz_id)

    def _execute(self, data, parent_data):
        # 更新任务状态
        task_id = data.get_one_of_inputs("task_id")
        operator = data.get_one_of_inputs("operator")
        bk_biz_id = data.get_one_of_inputs("bk_biz_id")
        Tasks.objects.filter(task_id=task_id).update(download_status=constants.DownloadStatus.DISTRIBUTING.value)
        task = Tasks.objects.get(task_id=task_id)
        extract_link: ExtractLink = ExtractLink.objects.filter(link_id=task.link_id).first()
        if not extract_link:
            raise Exception(_("提取链路不存在"))
        hosts = extract_link.extractlinkhost_set.all()
        try:
            transit_server: ExtractLinkHost = random.choice(hosts)
        except IndexError:
            raise Exception(_("请配置链路中转服务器"))
        file_target_path = f"{constants.TRANSIT_SERVER_DISTRIBUTION_PATH}{get_packed_dir_name('', task_id)}/[FILESRCIP]"
        # 将文件分发到中转服务器目录
        task_result = FileServer.file_distribution(
            file_source_list=data.get_one_of_inputs("file_source_list"),
            file_target_path=file_target_path,
            target_ip_list=[{"ip": transit_server.ip, "bk_cloud_id": transit_server.bk_cloud_id}],
            bk_biz_id=bk_biz_id,
            operator=operator,
            account=data.get_one_of_inputs("account"),
            task_name="[BKLOG] File Distribution By {}".format(data.get_one_of_inputs("username")),
        )

        task_instance_id = FileServer.get_task_id(task_result)
        data.outputs.task_instance_id = task_instance_id

        # 分发任务ID写入数据库
        Tasks.objects.filter(task_id=task_id).update(job_task_id=task_instance_id)

        # 以下代码为下载, 中转后打包组件传递数据
        data.outputs.distribution_ip = [transit_server]
        # 输出中转后打包步骤的文件路径和打包路径
        data.outputs.transit_server_file_path = [
            get_packed_dir_name(constants.TRANSIT_SERVER_DISTRIBUTION_PATH, task_id)
        ]
        data.outputs.transit_server_packing_file_path = constants.TRANSIT_SERVER_PACKING_PATH

        return True

    def _schedule(self, data, parent_data, callback_data=None):
        task_id = data.get_one_of_inputs("task_id")
        operator = data.get_one_of_inputs("operator")
        bk_biz_id = data.get_one_of_inputs("bk_biz_id")
        Tasks.objects.filter(task_id=task_id).update(download_status=constants.DownloadStatus.DISTRIBUTING.value)
        task_instance_id = data.get_one_of_outputs("task_instance_id")
        query_result = self._poll_status(task_instance_id, operator, bk_biz_id)

        # 判断脚本是否执行结束
        if not FileServer.is_finished_for_single_ip(query_result):
            data.outputs.ex_data = _("脚本正在执行中")
            return True

        # 判断文件分发是否成功
        ip_status = FileServer.get_ip_status(query_result)
        if ip_status != constants.JOB_SUCCESS_STATUS:
            raise Exception(_("文件分发异常({})".format(ip_status)))

        self.finish_schedule()
        return True


class FileDistributionComponent(Component):
    name = "FileDistributionComponent"
    code = "file_dist_comp"
    bound_service = FileDistributionService
