# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MonitorReportConfig(models.Model):
    """运营数据上报配置初始化"""

    data_id = models.IntegerField(_("监控数据源id"), blank=True, null=True)
    data_name = models.CharField(_("数据源名称"), max_length=64, unique=True)
    bk_biz_id = models.IntegerField(_("指定业务id"))
    table_id = models.CharField(_("结果表名"), max_length=128, blank=True, null=True)
    access_token = models.CharField(_("数据上报token"), max_length=128, blank=True, null=True)
    is_enable = models.BooleanField(_("数据源是否enable"), default=True)

    class Meta:
        verbose_name = _("运营数据上报配置")
        verbose_name_plural = _("运营数据上报配置")
