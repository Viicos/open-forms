# Generated by Django 2.2.20 on 2021-06-21 15:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0021_auto_20210618_1750"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="form",
            name="email_property_name",
        ),
    ]
