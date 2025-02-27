# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import importlib
import time
import logging
from collections import defaultdict
import arrow

from bk_monitor.constants import LOGGER_NAME
from bk_monitor.utils.metric import REGISTERED_METRICS

logger = logging.getLogger(LOGGER_NAME)


class MetricCollector(object):
    """
    实际采集
    """

    def __init__(self, collector_import_paths=None):
        if collector_import_paths:
            for key in collector_import_paths:
                importlib.import_module(key)

    def collect(self, namespaces=None):
        """
        采集入口
        """
        metric_methods = self.metric_filter(namespaces=namespaces)
        metric_groups = []
        for metric_method in metric_methods:
            try:
                begin_time = time.time()
                metric_groups.append(
                    {
                        "namespace": metric_method["namespace"],
                        "description": metric_method["description"],
                        "metrics": metric_method["method"](),
                        "date_name": metric_method["data_name"],
                    }
                )
                logger.info(
                    "[statistics_data] collect metric->[{}] took {} ms".format(
                        metric_method["namespace"], int((time.time() - begin_time) * 1000)
                    ),
                )
            except Exception as e:
                logger.exception(
                    "[statistics_data] collect metric->[{}] failed: {}".format(metric_method["namespace"], e)
                )

        res = defaultdict(list)
        for group in metric_groups:
            for metric in group["metrics"]:
                res[group["date_name"]].append(metric.to_bkmonitor_report(namespace=group["namespace"]))
        return res

    @classmethod
    def metric_filter(cls, namespaces=None):
        metric_methods = []
        time_now = arrow.now()
        time_now_minute = 60 * time_now.hour + time_now.minute
        for metric in REGISTERED_METRICS:
            if namespaces and metric["namespace"] not in namespaces:
                continue

            # 如果register_metric 有设置time_filter字段以及该字段符合当前时间所属周期才会被添加
            if metric["time_filter"] and time_now_minute % metric["time_filter"]:
                continue
            metric_methods.append(metric)
        return metric_methods
