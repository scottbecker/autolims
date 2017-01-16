# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-16 03:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autolims', '0005_auto_20170115_2241'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='autoprotocol',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='organization',
            name='subdomain',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='sample',
            name='barcode',
            field=models.IntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='cover',
            field=models.CharField(blank=True, choices=[(b'low_evaporation', b'low_evaporation'), (b'universal', b'universal'), (b'standard', b'standard')], max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='generated_by_run',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='generated_containers', related_query_name='generated_container', to='autolims.Run'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='label',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
    ]
