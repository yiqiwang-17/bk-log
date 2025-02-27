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

from celery.task import periodic_task, task
from celery.schedules import crontab

from apps.utils.log import logger
from apps.api.modules.bkdata_access import BkDataAccessApi
from apps.log_databus.constants import (
    BKDATA_DATA_SCENARIO,
    BKDATA_DATA_SCENARIO_ID,
    BKDATA_PERMISSION,
    BKDATA_TAGS,
    BKDATA_DATA_SOURCE_TAGS,
    BKDATA_DATA_REGION,
    BKDATA_DATA_SOURCE,
    BKDATA_DATA_SENSITIVITY,
    MAX_CREATE_BKDATA_DATA_ID_FAIL_COUNT,
    META_DATA_ENCODING,
    ADMIN_REQUEST_USER,
)
from apps.feature_toggle.plugins.constants import FEATURE_BKDATA_DATAID
from apps.log_databus.models import CollectorConfig
from apps.feature_toggle.handlers.toggle import FeatureToggleObject


@task(ignore_result=True)
def async_create_bkdata_data_id(collector_config_id: int):
    create_bkdata_data_id(CollectorConfig.objects.get(collector_config_id=collector_config_id))


def create_bkdata_data_id(collector_config: CollectorConfig):
    # 对应开关未开启
    toggle_switch = FeatureToggleObject.switch(name=FEATURE_BKDATA_DATAID)
    if not toggle_switch:
        return

    if not collector_config.bk_data_id or collector_config.bkdata_data_id:
        return

    # todo 待高级清洗上线英文名 该临时方案将被修改
    if not collector_config.table_id:
        return

    maintainers = {collector_config.updated_by, collector_config.created_by}
    maintainers.discard(ADMIN_REQUEST_USER)
    if not maintainers:
        raise BaseException(f"dont have enough maintainer only {ADMIN_REQUEST_USER}")

    BkDataAccessApi.deploy_plan_post(
        params={
            "bk_username": collector_config.get_updated_by(),
            "data_scenario": BKDATA_DATA_SCENARIO,
            "data_scenario_id": BKDATA_DATA_SCENARIO_ID,
            "permission": BKDATA_PERMISSION,
            "bk_biz_id": collector_config.bk_biz_id,
            "description": collector_config.description,
            "access_raw_data": {
                "tags": BKDATA_TAGS,
                "raw_data_name": collector_config.table_id.replace(".", "_"),
                "maintainer": ",".join(maintainers),
                "raw_data_alias": collector_config.collector_config_name,
                "data_source_tags": BKDATA_DATA_SOURCE_TAGS,
                "data_region": BKDATA_DATA_REGION,
                "data_source": BKDATA_DATA_SOURCE,
                "data_encoding": collector_config.data_encoding
                if collector_config.data_encoding
                else META_DATA_ENCODING,
                "sensitivity": BKDATA_DATA_SENSITIVITY,
                "description": collector_config.description,
                "preassigned_data_id": collector_config.bk_data_id,
            },
        }
    )
    collector_config.bkdata_data_id = collector_config.bk_data_id
    collector_config.save()


@periodic_task(run_every=crontab(minute="30", hour="3"))
def review_bkdata_data_id():
    """
    检测采集项bkdata_id: 处理未同步到数据平台的data_id
    """
    toggle_switch = FeatureToggleObject.switch(name=FEATURE_BKDATA_DATAID)
    if not toggle_switch:
        return
    collector_configs = CollectorConfig.objects.filter(bkdata_data_id__isnull=True)
    for collector_config in collector_configs:
        if collector_config.bkdata_data_id_sync_times >= MAX_CREATE_BKDATA_DATA_ID_FAIL_COUNT:
            logger.error(
                f"{collector_config.collector_config_name} "
                + f"创建bkdata_data_id超过最大重试次数: {MAX_CREATE_BKDATA_DATA_ID_FAIL_COUNT}"
            )
            continue

        try:
            create_bkdata_data_id(collector_config)
        except Exception as e:
            logger.error(f"{collector_config.collector_config_name} create bkdata data_id failed: {e}")
            collector_config.bkdata_data_id_sync_times += 1
        else:
            collector_config.bkdata_data_id_sync_times = 0

        collector_config.save()
