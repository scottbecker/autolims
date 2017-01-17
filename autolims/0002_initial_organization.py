# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-15 21:37
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion

def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Organization = apps.get_model("autolims", "Organization")
    db_alias = schema_editor.connection.alias
    Organization.objects.using(db_alias).bulk_create([
        Organization(name="Default Organization", subdomain='default')
    ])

def reverse_func(apps, schema_editor):
    # forwards_func() creates two Country instances,
    # so reverse_func() should delete them.
    Organization = apps.get_model("autolims", "Organization")
    db_alias = schema_editor.connection.alias
    Organization.objects.using(db_alias).filter(id=1).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('autolims', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
