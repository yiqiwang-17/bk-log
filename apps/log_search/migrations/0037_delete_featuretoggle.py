# Generated by Django 2.2.6 on 2021-07-13 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("log_search", "0036_auto_20210705_1624"),
    ]

    operations = [
        migrations.DeleteModel(
            name="FeatureToggle",
        ),
    ]
