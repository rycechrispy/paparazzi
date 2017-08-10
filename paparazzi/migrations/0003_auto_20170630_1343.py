# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-30 20:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paparazzi', '0002_auto_20170630_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='title',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='item',
            name='title_original',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]