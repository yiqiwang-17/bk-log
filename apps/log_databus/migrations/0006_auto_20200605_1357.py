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
# Generated by Django 1.11.23 on 2020-06-05 05:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("log_databus", "0005_auto_20191119_1049"),
    ]

    operations = [
        migrations.CreateModel(
            name="StorageCapacity",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("bk_biz_id", models.IntegerField(verbose_name="业务id")),
                ("storage_capacity", models.FloatField(verbose_name="容量")),
            ],
            options={
                "verbose_name": "公共集群容量限制",
                "verbose_name_plural": "存储集群容量限制",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="StorageUsed",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("bk_biz_id", models.IntegerField(verbose_name="业务id")),
                ("storage_cluster_id", models.IntegerField(verbose_name="集群ID")),
                ("storage_used", models.FloatField(verbose_name="已用容量")),
            ],
            options={
                "verbose_name": "业务已用容量",
                "verbose_name_plural": "业务已用容量",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.AlterField(
            model_name="collectorconfig",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="collectorconfig",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
        migrations.AlterUniqueTogether(
            name="storageused",
            unique_together={("bk_biz_id", "storage_cluster_id")},
        ),
    ]
