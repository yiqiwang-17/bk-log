# Generated by Django 2.2.6 on 2021-07-05 08:24

import apps.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("log_search", "0035_init_async_export"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logindexset",
            name="view_roles",
            field=apps.models.MultiStrSplitByCommaField(blank=True, max_length=255, null=True, verbose_name="查看权限"),
        ),
    ]
