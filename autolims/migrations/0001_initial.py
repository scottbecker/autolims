# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-17 17:16
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Aliquot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('well_idx', models.IntegerField(default=0)),
                ('volume_ul', models.CharField(default='0', max_length=200)),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AliquotEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effect_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('effect_type', models.CharField(choices=[('liquid_transfer_in', 'liquid_transfer_in'), ('liquid_transfer_out', 'liquid_transfer_out'), ('instruction', 'instruction')], default='liquid_transfer_in', max_length=200)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('affected_aliquot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliquot_effects', related_query_name='aliquot_effect', to='autolims.Aliquot')),
            ],
        ),
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('data_type', models.CharField(choices=[('image_plate', 'image_plate'), ('platereader', 'platereader'), ('measure', 'measure')], default='available', max_length=200)),
                ('sequence_no', models.IntegerField(default=0)),
                ('image', models.ImageField(blank=True, null=True, upload_to='autolims.DataImage/bytes/filename/mimetype')),
                ('file', models.FileField(blank=True, null=True, upload_to='autolims.DataFile/bytes/filename/mimetype')),
                ('json', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'data',
            },
        ),
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bytes', models.TextField()),
                ('filename', models.CharField(max_length=255)),
                ('mimetype', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='DataImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bytes', models.TextField()),
                ('filename', models.CharField(max_length=255)),
                ('mimetype', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Instruction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('sequence_no', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=200)),
                ('subdomain', models.CharField(blank=True, default='', max_length=200)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('bsl', models.IntegerField(default=1)),
                ('archived_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='projects', related_query_name='project', to='autolims.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1000, null=True)),
                ('status', models.CharField(choices=[('complete', 'complete'), ('accepted', 'accepted'), ('in_progress', 'in_progress'), ('aborted', 'aborted'), ('canceled', 'canceled')], default='available', max_length=200)),
                ('test_mode', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('aborted_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('flagged', models.BooleanField(default=False)),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('autoprotocol', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', related_query_name='run', to='autolims.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('container_type_id', models.CharField(choices=[(b'384-pcr', b'384-pcr'), (b'384-flat-white-white-nbs', b'384-flat-white-white-nbs'), (b'96-deep', b'96-deep'), (b'96-flat-clear-clear-tc', b'96-flat-clear-clear-tc'), (b'6-flat-tc', b'6-flat-tc'), (b'96-flat', b'96-flat'), (b'96-pcr', b'96-pcr'), (b'24-deep', b'24-deep'), (b'384-flat', b'384-flat'), (b'96-flat-uv', b'96-flat-uv'), (b'384-echo', b'384-echo'), (b'384-flat-white-white-tc', b'384-flat-white-white-tc'), (b'screw-cap-1.8', b'screw-cap-1.8'), (b'384-v-clear-clear', b'384-v-clear-clear'), (b'micro-2.0', b'micro-2.0'), (b'6-flat', b'6-flat'), (b'96-flat-tc', b'96-flat-tc'), (b'micro-1.5', b'micro-1.5'), (b'1-flat', b'1-flat'), (b'96-v-kf', b'96-v-kf'), (b'384-round-clear-clear', b'384-round-clear-clear'), (b'384-flat-clear-clear', b'384-flat-clear-clear'), (b'96-deep-kf', b'96-deep-kf'), (b'384-flat-white-white-lv', b'384-flat-white-white-lv')], max_length=200)),
                ('barcode', models.IntegerField(blank=True, db_index=True, null=True, unique=True)),
                ('cover', models.CharField(blank=True, choices=[(b'low_evaporation', b'low_evaporation'), (b'universal', b'universal'), (b'standard', b'standard')], max_length=200, null=True)),
                ('test_mode', models.BooleanField(default=False)),
                ('label', models.CharField(blank=True, db_index=True, default='', max_length=1000)),
                ('storage_condition', models.CharField(blank=True, choices=[(b'cold_4', b'cold_4'), (b'cold_20', b'cold_20'), (b'cold_80', b'cold_80'), (b'warm_37', b'warm_37'), (b'ambient', b'ambient')], default=b'ambient', max_length=200, null=True)),
                ('status', models.CharField(choices=[('available', 'available'), ('destroyed', 'destroyed'), ('returned', 'returned'), ('inbound', 'inbound'), ('outbound', 'outbound'), ('pending_destroy', 'pending_destroy')], default='available', max_length=200)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('generated_by_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='generated_containers', related_query_name='generated_container', to='autolims.Run')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='containers', related_query_name='container', to='autolims.Organization')),
            ],
        ),
        migrations.AddField(
            model_name='run',
            name='refs',
            field=models.ManyToManyField(blank=True, null=True, related_name='related_runs', related_query_name='related_run', to='autolims.Sample'),
        ),
        migrations.AddField(
            model_name='instruction',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instructions', related_query_name='instruction', to='autolims.Run'),
        ),
        migrations.AddField(
            model_name='data',
            name='instruction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data', related_query_name='data', to='autolims.Instruction'),
        ),
        migrations.AddField(
            model_name='data',
            name='run',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data', related_query_name='data', to='autolims.Run'),
        ),
        migrations.AddField(
            model_name='aliquoteffect',
            name='generating_instruction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliquot_effects', related_query_name='aliquot_effect', to='autolims.Instruction'),
        ),
        migrations.AddField(
            model_name='aliquot',
            name='container',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliquots', related_query_name='aliquot', to='autolims.Sample'),
        ),
        migrations.AlterUniqueTogether(
            name='instruction',
            unique_together=set([('run', 'sequence_no')]),
        ),
        migrations.AlterUniqueTogether(
            name='data',
            unique_together=set([('run', 'sequence_no')]),
        ),
    ]